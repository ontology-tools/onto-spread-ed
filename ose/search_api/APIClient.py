import abc
import asyncio
import json
import logging
import re
import urllib
from abc import ABCMeta
from itertools import groupby
from typing import Union, List, Literal, Optional, Dict, Tuple, Any, TypeVar

import aiohttp
import async_lru
from attr import dataclass

from ose.model.Result import Result
from ose.model.Term import Term
from ose.model.TermIdentifier import TermIdentifier
from ose.search_api.HttpError import HttpError

T = TypeVar('T')


@dataclass
class APIPage:
    items: List[T]
    page: int
    total_items: int
    next_page: int
    first_page: int
    last_page: int


class APIClient(abc.ABC, metaclass=ABCMeta):
    _logger = logging.getLogger(__name__)

    _term_link_to_relation_mapping: Dict[str, Tuple[TermIdentifier, Literal["single", "multiple", "multiple-per-line"]]]

    def __init__(self, api_url: str, session: aiohttp.ClientSession, auth_token: Optional[str] = None, debug=False):
        self._auth_token = auth_token
        self._base = api_url
        self._session = session
        self._default_params = {"test": "1"} if debug else {}

    def _request(self,
                 sub_url: Union[str, List[str]],
                 method: Literal["get", "post", "put", "patch", "delete"],
                 data: Optional[Dict] = None,
                 headers: Optional[Dict] = None,
                 query_params: Optional[Dict[str, str]] = None) -> aiohttp.client._RequestContextManager:
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        if query_params is None:
            query_params = {} if method == "get" else self._default_params

        default_headers = {
            "accept": "application/ld+json",
            "Content-Type": "application/ld+json"
        }

        if self._auth_token is not None:
            default_headers["X-AUTH-TOKEN"] = self._auth_token

        url = self._base
        if isinstance(sub_url, list):
            url = urllib.parse.urljoin(url, "/".join(sub_url))
        else:
            url = urllib.parse.urljoin(url, sub_url)

        query_string = urllib.parse.urlencode(query_params)
        if query_string != "":
            url += "?" + query_string

        headers = {**default_headers, **headers}
        if method != "get":
            self._logger.info(f"{method} {json.dumps(data)}")

            # return self._session.request("get", "https://example.com/")
        # else:
        return self._session.request(method, url, headers=headers, json=data)

    def convert_to_api_term(self, term: Term, with_references=True) -> Dict:
        data = {
            "id": term.id.strip(),
            "uri": f"/terms/{term.id.strip()}",
            "label": term.label.strip(),
            **dict([(k,
                     (((lambda x: x) if multiplicity == "multiple" else "\n".join)(term.get_relation_values(i)))
                     if multiplicity.startswith("multiple") else term.get_relation_value(i))
                    for k, (i, multiplicity) in self._term_link_to_relation_mapping.items()]),
        }

        if data['curationStatus'] in ['To Be Discussed', 'In Discussion', None]:
            data['curationStatus'] = 'Proposed'

        definition_source = self._merge_definition_source_and_id(term)
        if definition_source:
            data["definitionSource"] = definition_source

        data['eCigO'] = data.get('eCigO', 'false') in ["True", "true", "TRUE", "1"]
        data['fuzzySet'] = data.get('fuzzySet', 'false') in ["True", "true", "TRUE", "1"]

        if data.get('curationStatus', None) is None:
            data['curationStatus'] = "Proposed"
        data['curationStatus'] = data['curationStatus'].lower()

        if with_references:
            def key_fn(r: Union[Tuple[TermIdentifier, Any], TermIdentifier]) -> str:
                return (r[0] if isinstance(r, tuple) else r).label

            relations: List[Tuple[TermIdentifier, TermIdentifier]] = [(r, v) for r, v in term.relations if
                                                                      isinstance(v, TermIdentifier) and v.is_resolved()]
            relations.sort(key=key_fn)

            data = {
                **data,
                "parentTerm": f"/terms/{term.sub_class_of[0].id}",
                "logicalDefinition": next(iter(term.equivalent_to), None),
                "termLinks": [{
                    "type": r,
                    "linkedTerms": [f"/terms/{e[1].id}" for e in g]
                } for r, g in groupby(relations, key_fn)]
            }

        return data

    async def convert_from_api_term(self, data: Dict, with_references=True) -> Term:
        rev = data["termRevisions"][0]

        i: str = data["id"]
        label: str = rev["label"]

        parent_term = rev.get("parentTerm", None)
        parents: List[TermIdentifier] = [TermIdentifier(id=parent_term.split("/")[-1])] if parent_term else []

        logical_definition = rev.get("logicalDefinition", None)
        equivalent_to: List[str] = [logical_definition] if logical_definition else []

        disjoint_with = []

        relations: List[Tuple[TermIdentifier, Any]] = []
        if with_references:
            async with self._request([rev["@id"], "term_links"], "get") as response:
                term_links = (await response.json())["hydra:member"]
                relations = [
                    (TermIdentifier(label=link["type"]),
                     TermIdentifier(linked["id"], linked["termRevisions"][0]["label"]))
                    for link in term_links
                    for linked in link["linkedTerms"]
                ]

        relations += [(identifier, v)
                      for key, (identifier, multiplicity) in self._term_link_to_relation_mapping.items() if key in rev
                      for v in (
                          ((lambda x: x) if multiplicity == "multiple" else str.splitlines)(rev[key])
                          if multiplicity.startswith("multiple") else [rev[key]])
                      ]

        relations += [(identifier, v)
                      for key, (identifier, multiplicity) in self._term_link_to_relation_mapping.items() if
                      key in data and key not in rev
                      for v in (
                          ((lambda x: x) if multiplicity == "multiple" else str.splitlines)(data[key])
                          if multiplicity.startswith("multiple") else [data[key]])
                      ]
        definition_source = rev.get("definitionSource", None)
        if definition_source is not None:
            parts = definition_source.split("\n")
            if len(parts) == 1:
                relations.append((TermIdentifier(id="IAO:0000119", label="definition source"), parts[0]))
            elif len(parts) == 2:
                relations += [
                    (TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy"), parts[0]),
                    (TermIdentifier(id="IAO:0000119", label="definition source"), parts[1])
                ]

        return Term(i, label, ("web", -1), relations, parents, equivalent_to, disjoint_with)

    @async_lru.alru_cache(maxsize=None)
    async def _get_term(self, term: str) -> Optional[Dict]:
        async with self._request(["terms", term], "get") as r:
            if r.status == 404:
                return None

            if not r.ok:
                raise HttpError(r.status,
                                f"{r.status}, message={r.reason!r}, url={r.request_info.real_url!r}",
                                await r.json())

            return await r.json()

    async def get_term(self, term: Union[Term, str, TermIdentifier], with_references=True) -> Optional[Term]:
        term_id = term.id if isinstance(term, Term) or isinstance(term, TermIdentifier) else term

        data = await self._get_term(term_id)

        if data is None:
            return None

        return await self.convert_from_api_term(data, with_references)

    async def create_term(self, term: Term):
        data = self.convert_to_api_term(term)

        async with self._request("terms", "post", data) as r:
            if not r.ok:
                raise HttpError(r.status,
                                f"{r.status}, message={r.reason!r}, url={r.request_info.real_url!r}",
                                await r.json())

    async def declare_term(self, term: Union[Term, TermIdentifier]) -> Result[Union[bool]]:
        exists = (await self.get_term(term, with_references=False)) is not None
        if exists:
            return Result(False)

        data = self.convert_to_api_term(term, False)

        async with self._request("terms", "post", data) as r:

            if not r.ok:
                result = Result()
                error = await r.text()
                result.error(status_code=r.status, body=error)
                self._logger.error(f"Failed to declare term '{term.label} ({term.id})': {error}")
                return result

            return Result(True)

    async def update_term(self, term: Term, msg: str, with_references=True):
        existing = await self.get_term(term, with_references)
        if existing is not None:
            if not self.terms_equal(existing, term):
                api_term = self.convert_to_api_term(term)
                api_term['revisionMessage'] = msg

                async with self._request(["terms", term.id], "put", api_term, headers={
                    "Content-Type": "application/json"
                }) as r:
                    if not r.ok:
                        raise HttpError(r.status,
                                        f"{r.status}, message={r.reason!r}, url={r.request_info.real_url!r}",
                                        await r.json())

    def delete_term(self, term: Union[Term, str, TermIdentifier]):
        pass

    def _merge_definition_source_and_id(self, term: Term) -> Optional[str]:
        defined_by = term.get_relation_value(TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy"))
        definition_source = term.get_relation_value(TermIdentifier(id="IAO:0000119", label="definition source"))
        return "\n".join(d for d in [defined_by, definition_source] if d is not None)

    def _terms_equal(self, ignore_if_not_exists: List[str], new: Term, old: Term):
        def value_eq(v1, v2) -> bool:
            if isinstance(v1, bool):
                return (str(v2).lower().strip() in ['true', '1']) == v1
            if isinstance(v2, bool):
                return (str(v1).lower().strip() in ['true', '1']) == v2
            if isinstance(v1, str) and isinstance(v2, str):
                return v1.lower().strip() == v2.lower().strip()
            if v1 is None and v2 == 'None' or v2 is None and v1 == 'None':
                return True

            if isinstance(v1, TermIdentifier) and isinstance(v2, TermIdentifier):
                if v1.id is None or v2.id is None:
                    return v1.label == v2.label
                else:
                    return v1.id == v2.id
            if isinstance(v1, list) and isinstance(v2, list):
                return len(v1) == len(v2) and all(any(value_eq(x1, x2) for x2 in v2) for x1 in v1)

            return v1 == v2

        result = True
        relations_old = dict(
            [(k, [e[1] for e in g]) for k, g in groupby(sorted(old.relations), key=lambda x: x[0].label)])
        relations_new = dict(
            [(k, [e[1] for e in g]) for k, g in groupby(sorted(new.relations), key=lambda x: x[0].label)])
        for r, v in relations_old.items():
            if r in ["rdfs:isDefinedBy", "definition source", "example of usage"]:
                continue

            if r in relations_new:
                if not value_eq(relations_new[r], v):
                    self._logger.debug(f"DIFF <{r}>:\n  {v}\n  {relations_new[r]}")
                    result = False
            else:
                if r not in ignore_if_not_exists:
                    self._logger.debug(f"DELETED <{r}>: {v}")
                    result = False
        for r, v in relations_new.items():
            if r in ["rdfs:isDefinedBy", "definition source"]:
                continue

            if r not in relations_old:
                if r not in ignore_if_not_exists:
                    self._logger.debug(f"CREATED <{r}>: {v}")
                    result = False
        old_definition_source = self._merge_definition_source_and_id(old)
        new_definition_source = self._merge_definition_source_and_id(new)
        if not (value_eq(old_definition_source, new_definition_source)):
            self._logger.debug(f"DIFF <definitionSource>\n  {[old_definition_source]}\n  {[new_definition_source]}")
            result = False
        old_examples = old.get_relation_values(TermIdentifier(label="example of usage"))
        new_examples = new.get_relation_values(TermIdentifier(label="example of usage"))
        if isinstance(old_examples, list):
            old_examples = "\n".join(old_examples)
        if isinstance(new_examples, list):
            new_examples = "\n".join(new_examples)
        if not (value_eq(old_examples, new_examples)):
            self._logger.debug(f"DIFF <examples>\n  {[old_examples]}\n  {[new_examples]}")
            result = False
        if not (old.id == new.id):
            self._logger.debug(f"DIFF <id>\n  {old.id}\n  {new.id}")
            result = False
        if not (value_eq(old.label, new.label)):
            self._logger.debug(f"DIFF <label>\n  {old.label}\n  {new.label}")
            result = False
        if not (value_eq(old.sub_class_of, new.sub_class_of)):
            self._logger.debug(f"DIFF <sub_class_of>\n  {old.sub_class_of}\n  {new.sub_class_of}")
            result = False
        if not (value_eq(old.equivalent_to, new.equivalent_to)):
            self._logger.debug(f"DIFF <equivalent_to>\n  {old.equivalent_to}\n  {new.equivalent_to}")
            result = False
        # # Apparently this is not used by BCIOSearch
        # if not (value_eq(old.disjoint_with, new.disjoint_with)):
        #     self._logger.debug(f"DIFF <disjoint_with>\n  {old.disjoint_with}\n  {new.disjoint_with}")
        #     result = False
        return result

    async def get_terms(self, page: int, items_per_page: int = 50) -> APIPage:
        r = await self._request(f"/terms?page={page}&itemsPerPage={items_per_page}", "get")

        r.raise_for_status()

        data = await r.json()

        view = data.get("hydra:view", dict())
        next_page_m = re.search(r"page=(\d+)", view.get("hydra:next", ""))
        next_page = int(next_page_m.group(1)) if next_page_m is not None else None
        first_page_m = re.search(r"page=(\d+)", view.get("hydra:first", ""))
        first_page = int(first_page_m.group(1)) if first_page_m is not None else None
        last_page_m = re.search(r"page=(\d+)", view.get("hydra:last", ""))
        last_page = int(last_page_m.group(1)) if last_page_m is not None else None

        total_items = data.get("hydra:totalItems", -1)

        items = await asyncio.gather(
            *(self.convert_from_api_term(term, False) for term in data.get("hydra:member", [])))

        return APIPage(items, page, total_items, next_page, first_page, last_page)
