from typing import Literal, Dict, Tuple

from aiohttp import ClientSession

from .APIClient import APIClient
from ..model.Term import Term
from ..model.TermIdentifier import TermIdentifier


class AddictOVocabClient(APIClient):
    _session: ClientSession

    _term_link_to_relation_mapping: Dict[
        str, Tuple[TermIdentifier, Literal["single", "multiple", "multiple-per-line"]]] = {
        "synonyms": (TermIdentifier(id="IAO:0000118", label="alternative label"), "multiple"),
        "definition": (TermIdentifier(id="IAO:0000115", label="definition"), "single"),
        "informalDefinition": (TermIdentifier(label="informalDefinition"), "single"),
        "addictoSubOntology": (TermIdentifier(label="lowerLevelOntology"), "multiple"),
        "curatorNote": (TermIdentifier(id="IAO:0000232", label="curator note"), "single"),
        "curationStatus": (TermIdentifier(id="IAO:0000114", label="has curation status"), "single"),
        "comment": (TermIdentifier(id="rdfs:comment", label="rdfs:comment"), "single"),
        "examples": (TermIdentifier(id="IAO:0000112", label="example of usage"), "multiple-per-line"),
        "fuzzySet": (TermIdentifier(label="fuzzySet"), "single"),
        "fuzzyExplanation": (TermIdentifier(label="fuzzyExplanation"), "single"),
        "crossReferences": (TermIdentifier(label="crossReference"), "multiple"),
    }

    def convert_to_api_term(self, term: Term, with_references=True) -> Dict:
        data = super().convert_to_api_term(term, with_references)

        if "addictoSubOntology" in data and data["addictoSubOntology"] is not None:
            lower_level_ontologies = [d.lower().strip() for d in data["addictoSubOntology"]]
            if "upper level" in lower_level_ontologies:
                lower_level_ontologies.remove("upper level")

            data["addictoSubOntology"] = lower_level_ontologies

        return data

    async def convert_from_api_term(self, data: Dict, with_references=True) -> Term:
        term = await super().convert_from_api_term(data, with_references)

        term.relations = [(r, bool(int(v))) if r.id is None and r.label in ["eCigO", "fuzzySet"] else (r, v) for r, v in
                          term.relations]

        return term

    def terms_equal(self, old: Term, new: Term) -> bool:
        ignore_if_not_exists = [
            "informalDefinition",
            "addictoSubOntology",
            "fuzzySet",
            "fuzzyExplanation",
            "crossReference",
            "eCigO"
        ]

        return self._terms_equal(ignore_if_not_exists, new, old)
