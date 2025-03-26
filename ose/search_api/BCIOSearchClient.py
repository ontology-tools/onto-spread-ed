import logging
from typing import Literal, Dict, Tuple

from aiohttp import ClientSession

from .APIClient import APIClient
from ..model.Term import Term
from ..model.TermIdentifier import TermIdentifier


class BCIOSearchClient(APIClient):
    _session: ClientSession
    _logger = logging.getLogger(__name__)

    _term_link_to_relation_mapping: Dict[
        str, Tuple[TermIdentifier, Literal["single", "multiple", "multiple-per-line"]]] = {
        "synonyms": (TermIdentifier(id="IAO:0000118", label="alternative label"), "multiple"),
        "definition": (TermIdentifier(id="IAO:0000115", label="definition"), "single"),
        "informalDefinition": (TermIdentifier(label="informalDefinition"), "single"),
        "lowerLevelOntology": (TermIdentifier(label="lowerLevelOntology"), "multiple"),
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

        if "lowerLevelOntology" in data and data["lowerLevelOntology"] is not None:
            lower_level_ontologies = [d.lower().strip() for d in data["lowerLevelOntology"]]
            if "upper level" in lower_level_ontologies:
                lower_level_ontologies.remove("upper level")

            data["lowerLevelOntology"] = lower_level_ontologies

        return data

    def terms_equal(self, old: Term, new: Term) -> bool:
        ignore_if_not_exists = [
            "informalDefinition",
            "lowerLevelOntology",
            "fuzzySet",
            "fuzzyExplanation",
            "crossReference"
        ]

        return self._terms_equal(ignore_if_not_exists, new, old)
