import functools
import json
import logging
import urllib.parse
import urllib
from itertools import groupby
from typing import Optional, Union, Literal, Dict, List, Any, Tuple

import requests
from requests import Response

from onto_spread_ed.model.Result import Result
from onto_spread_ed.model.Term import Term
from onto_spread_ed.model.TermIdentifier import TermIdentifier


class BCIOSearchClient:
    _logger = logging.getLogger(__name__)

    _term_link_to_relation_mapping: Dict[str, Tuple[TermIdentifier, Literal["single", "multiple"]]] = {
        "synonyms": (TermIdentifier(id="IAO:0000118", label="alternative label"), "multiple"),
        "definition": (TermIdentifier(id="IAO:0000115", label="definition"), "single"),
        "informalDefinition": (TermIdentifier(label="informalDefinition"), "single"),
        "lowerLevelOntology": (TermIdentifier(label="lowerLevelOntology"), "single"),
        "curatorNote": (TermIdentifier(id="IAO:0000232", label="curator note"), "single"),
        "curationStatus": (TermIdentifier(id="IAO:0000114", label="has curation status"), "single"),
        "comment": (TermIdentifier(id="rdfs:comment", label="rdfs:comment"), "single"),
        "examples": (TermIdentifier(id="IAO:0000112", label="example of usage"), "single"),
        "fuzzySet": (TermIdentifier(label="fuzzySet"), "single"),
        "fuzzyExplanation": (TermIdentifier(label="fuzzyExplanation"), "single"),
        "crossReferences": (TermIdentifier(label="crossReference"), "multiple"),
    }

    def __init__(self, api_url: str, auth_token: Optional[str] = None, debug=False):
        self._auth_token = auth_token
        self._base = api_url
        self._default_params = {"test": "1"} if debug else {}

    def _request(self,
                 sub_url: Union[str, List[str]],
                 method: Literal["get", "post", "put", "patch", "delete"],
                 data: Optional[Dict] = None,
                 headers: Optional[Dict] = None,
                 query_params: Optional[Dict[str, str]] = None) -> Response:
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        if query_params is None:
            query_params = {} if method == "get" else self._default_params

        default_headers = {
            "accept": "application/ld+json",
            "Content-Type": "application/ld+json",
            "X-AUTH-TOKEN": self._auth_token
        }

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
            # response = Response()
            # response.status_code = 200
            # return response
            # else:
        return requests.request(method, url, headers=headers, json=data)

    def _convert_to_api_term(self, term: Term, with_references=True) -> Dict:
        data = {
            "id": term.id.strip(),
            "uri": f"/terms/{term.id.strip()}",
            "label": term.label.strip(),
            **dict([(k, term.get_relation_values(id) if multiplicity == "multiple" else term.get_relation_value(id))
                    for k, (id, multiplicity) in self._term_link_to_relation_mapping.items()]),
        }

        if data['curationStatus'] in ['To Be Discussed','In Discussion', None]:
            data['curationStatus'] = 'Proposed'

        if "lowerLevelOntology" in data and data["lowerLevelOntology"] is not None:
                lower_level_ontology = data["lowerLevelOntology"].lower().strip()
                if lower_level_ontology == "upper level":
                    data["lowerLevelOntology"] = None
                else:
                    data["lowerLevelOntology"] = lower_level_ontology

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

            relations: List[Tuple[TermIdentifier, TermIdentifier]] = [(r, v) for r, v in term.relations if isinstance(v, TermIdentifier) and v.is_resolved()]
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

    def _merge_definition_source_and_id(self, term: Term) -> Optional[str]:
        defined_by = term.get_relation_value(TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy"))
        definition_source = term.get_relation_value(TermIdentifier(id="IAO:0000119", label="definition source"))
        return "\n".join(d for d in [defined_by, definition_source] if d is not None)

    def _convert_from_api_term(self, data: Dict, with_references=True) -> Term:
        rev = data["termRevisions"][0]

        id: str = data["id"]
        label: str = rev["label"]

        parent_term = rev.get("parentTerm", None)
        parents: List[TermIdentifier] = [TermIdentifier(id=parent_term.split("/")[-1])] if parent_term else []

        logical_definition = rev.get("logicalDefinition", None)
        equivalent_to: List[str] = [logical_definition] if logical_definition else []

        disjoint_with = []

        relations: List[Tuple[TermIdentifier, Any]] = []
        if with_references:
            term_links = self._request([rev["@id"], "term_links"], "get").json()["hydra:member"]
            relations = [
                (TermIdentifier(label=link["type"]), TermIdentifier(linked["id"], linked["termRevisions"][0]["label"]))
                for link in term_links
                for linked in link["linkedTerms"]
            ]

        relations += [(identifier, v)
                      for key, (identifier, multiplicity) in self._term_link_to_relation_mapping.items() if key in rev
                      for v in (rev[key] if multiplicity == "multiple" else [rev[key]])
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

        return Term(id, label, ("web", -1), relations, parents, equivalent_to, disjoint_with)

    @functools.lru_cache(maxsize=None)
    def _get_term(self, term: str) -> Optional[Dict]:
        r = self._request(["terms", term], "get")

        if r.status_code == 404:
            return None

        r.raise_for_status()

        return r.json()

    def get_term(self, term: Union[Term, str, TermIdentifier], with_references=True) -> Optional[Term]:
        term_id = term.id if isinstance(term, Term) or isinstance(term, TermIdentifier) else term

        data = self._get_term(term_id)

        if data is None:
            return None

        return self._convert_from_api_term(data, with_references)

    def create_term(self, term: Term):
        data = self._convert_to_api_term(term)

        response = self._request("terms", "post", data)

        response.raise_for_status()

    def declare_term(self, term: Union[Term, TermIdentifier]) -> Result[Union[Term, Tuple]]:
        exists = self.get_term(term, with_references=False) is not None
        if exists:
            return Result(())

        data = self._convert_to_api_term(term, False)

        r = self._request("terms", "post", data)

        if not r.ok:
            result = Result()
            result.error(status_code=r.status_code, body=r.content)
            return result

        return Result(r)

    def _terms_equal(self, old: Term, new: Term) -> bool:
        ignore_if_not_exists = [
            "informalDefinition",
            "lowerLevelOntology",
            "fuzzySet",
            "fuzzyExplanation",
            "crossReference"
        ]

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
                return v1.id == v2.id
            if isinstance(v1, list) and isinstance(v2, list):
                return len(v1) == len(v2) and all(any(value_eq(x1, x2) for x2 in v2) for x1 in v1)

            return v1 == v2

        result = True

        relations_old = dict([(k, [e[1] for e in g]) for k, g in groupby(sorted(old.relations), key=lambda x: x[0])])
        relations_new = dict([(k, [e[1] for e in g]) for k, g in groupby(sorted(new.relations), key=lambda x: x[0])])

        for r, v in relations_old.items():
            if r.label in ["rdfs:isDefinedBy", "definition source"]:
                continue

            if r in relations_new:
                if not value_eq(relations_new[r], v):
                    self._logger.debug(f"DIFF <{r}>:\n  {v}\n  {relations_new[r]}")
                    result = False
            else:
                if r.label not in ignore_if_not_exists:
                    self._logger.debug(f"DELETED <{r}>: {v}")
                    result = False

        for r, v in relations_new.items():
            if r.label in ["rdfs:isDefinedBy", "definition source"]:
                continue

            if r not in relations_old:
                if r.label not in ignore_if_not_exists:
                    self._logger.debug(f"CREATED <{r}>: {v}")
                    result = False

        old_definition_source = self._merge_definition_source_and_id(old)
        new_definition_source = self._merge_definition_source_and_id(new)

        if not (value_eq(old_definition_source, new_definition_source)):
            self._logger.debug(f"DIFF <definitionSource>\n  {[old_definition_source]}\n  {[new_definition_source]}")
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

    def update_term(self, term: Term, msg: str, with_references=True):
        existing = self.get_term(term, with_references)
        if existing is not None:
            if not self._terms_equal(existing, term):
                api_term = self._convert_to_api_term(term)
                api_term['revisionMessage'] = msg
                test = True
                if test:
                    response = self._request(["terms", term.id], "put", api_term, headers={
                        "Content-Type": "application/json"
                    })

                    response.raise_for_status()

    def delete_term(self, term: Union[Term, str, TermIdentifier]):
        pass