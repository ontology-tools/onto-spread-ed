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

    _term_link_to_relation_mapping = {
        "definition": TermIdentifier(id="IAO:0000115", label="definition"),
        "definitionSource": TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy"),
        "informalDefinition": TermIdentifier(label="informalDefinition"),
        "lowerLevelOntology": TermIdentifier(label="lowerLevelOntology"),
        "curatorNote": TermIdentifier(id="IAO:0000232", label="curator note"),
        "comment": TermIdentifier(id="rdfs:comment", label="rdfs:comment"),
        "examples": TermIdentifier(id="IAO:0000112", label="example of usage"),
        "fuzzySet": TermIdentifier(label="fuzzySet"),
        "fuzzyExplanation": TermIdentifier(label="fuzzyExplanation"),
        "crossReference": TermIdentifier(label="crossReference"),
    }

    def __init__(self, api_url: str, auth_token: Optional[str] = None):
        self._auth_token = auth_token
        self._base = api_url

    def _request(self,
                 sub_url: Union[str, List[str]],
                 method: Literal["get", "post", "patch", "delete"],
                 data: Optional[Dict] = None,
                 headers: Optional[Dict] = None) -> Response:
        if data is None:
            data = {}
        if headers is None:
            headers = {}
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

        headers = {**default_headers, **headers}
        if method == "get":
            return requests.request(method, url, headers=headers, json=data)
        else:
            self._logger.info(f"Would {method} {url} with {json.dumps(data)}")
            response = Response()
            response.status_code = 200
            return response

    def _convert_to_api_term(self, term: Term, with_references=True) -> Dict:
        data = {
            "id": term.id,
            "label": term.label,
            "synonyms": term.synonyms,
            **dict([(k, term.get_relation_value(id))
                    for k, id in self._term_link_to_relation_mapping.items()
                    if term.get_relation_value(id) is not None])
        }

        if with_references:
            key_fn = lambda r: (r[0] if isinstance(r, tuple) else r).label

            relations = [r for r, v in term.relations if isinstance(r, TermIdentifier) and not r.is_unresolved()]
            relations.sort(key=key_fn)

            data = {
                **data,
                "parentTerm": term.sub_class_of[0].id,
                "logicalDefinition": next(iter(term.equivalent_to), None),
                "termLinks": [{
                    "type": r,
                    "linkedTerms": [v for _, v in g]
                } for r, g in groupby(relations, key_fn)]
            }

            data['eCigO'] = data.get('eCigO', "false").lower() in ["true", "1"]
            data['fuzzySet'] = data.get('fuzzySet', "false").lower() in ["true", "1"]

            if 'curationStatus' not in data:
                data['curationStatus'] = "Proposed"

        return data

    def _convert_from_api_term(self, data: Dict, with_references=True) -> Term:
        rev = data["termRevisions"][0]

        id: str = data["id"]
        label: str = rev["label"]
        synonyms: List[str] = rev.get("synonyms", [])

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

        relations += [(identifier, rev[key]) for key, identifier in self._term_link_to_relation_mapping.items() if
                      key in rev]

        definition = rev.get("definition", None)
        if definition is not None:
            relations.append((TermIdentifier(id="IAO:0000115", label="definition"), definition))

        definition_source = rev.get("definition", None)
        if definition_source is not None:
            relations.append((TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy"), definition_source))

        return Term(id, label, synonyms, ("web", -1), relations, parents, equivalent_to, disjoint_with)

    def get_term(self, term: Union[Term, str, TermIdentifier], with_references=True) -> Optional[Term]:
        term_id = term.id if isinstance(term, Term) or isinstance(term, TermIdentifier) else term
        r = self._request(["terms", term_id], "get")

        if r.status_code == 404:
            return None

        r.raise_for_status()

        data = r.json()

        return self._convert_from_api_term(data, with_references)

    def create_term(self, term: Term):
        data = self._convert_to_api_term(term)

        self._request("terms", "post", data)

    def declare_term(self, term: Union[Term, TermIdentifier]) -> Result[Term]:
        exists = self.get_term(term, with_references=False) is not None
        if exists:
            return Result()

        data = self._convert_to_api_term(term, False)

        r = self._request("terms", "post", data)

        if not r.ok:
            result = Result()
            result.error(status_code=r.status_code, body=r.content)
            return result

        return Result(r)

    def update_term(self, term: Term, msg: str, with_references=True):
        existing = self.get_term(term)
        if existing is not None:
            if existing != term:
                api_term = self._convert_to_api_term(term)
                api_term['revisionMessage'] = msg
                self._request("terms", "patch", api_term, headers={
                    "Content-Type": "application/merge-patch+json"
                })

    def delete_term(self, term: Union[Term, str, TermIdentifier]):
        pass
