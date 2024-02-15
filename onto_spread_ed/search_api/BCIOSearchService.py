import logging
import os
from typing import List, Callable, Optional, Tuple

import pyhornedowl
import requests
from requests import HTTPError

from .APIService import APIService
from .BCIOSearchClient import BCIOSearchClient
from ..model.ExcelOntology import ExcelOntology
from ..model.Result import Result
from ..model.Term import Term
from ..model.TermIdentifier import TermIdentifier

PROP_BCIO_SEARCH_API_PATH = "BCIO_SEARCH_API_PATH"
PROP_BCIO_SEARCH_API_AUTH_TOKEN = "BCIO_SEARCH_API_AUTH_TOKEN"

BCIO_SEARCH_RELEASED_EXTERNALS_OWL = "https://raw.githubusercontent.com/HumanBehaviourChangeProject/ontologies/master/Upper%20Level%20BCIO/bcio_external.owl"


class BCIOSearchService(APIService):
    _api_client: BCIOSearchClient
    _logger = logging.getLogger(__name__)

    def __init__(self, config: dict):
        super().__init__(config)

        path = config.get(PROP_BCIO_SEARCH_API_PATH)
        authtoken = config.get(PROP_BCIO_SEARCH_API_AUTH_TOKEN, os.environ.get(PROP_BCIO_SEARCH_API_AUTH_TOKEN, None))

        self._config = config

        self._api_client = BCIOSearchClient(path, authtoken)

    def update_api(self, ontology: ExcelOntology, revision_message: str,
                   update_fn: Optional[Callable[[int, int, str], None]] = None) -> Result[Tuple]:
        result = Result()
        response = requests.get(BCIO_SEARCH_RELEASED_EXTERNALS_OWL)
        external_ontology = pyhornedowl.open_ontology(response.text)

        for [prefix, iri] in self._config["PREFIXES"]:
            external_ontology.add_prefix_mapping(prefix, iri)

        total = len(external_ontology.get_classes()) + len(ontology.terms())
        step = 0

        queue: List[Term] = []
        for term_iri in external_ontology.get_classes():
            step += 1
            if update_fn:
                update_fn(step, total, f"External - {term_iri}")

            term_id = external_ontology.get_id_for_iri(term_iri)
            if term_id is None:
                self._logger.warning(f"Term has no id {term_iri}")
                continue

            term = ontology.term_by_id(term_id)
            if term is None:
                ext_label = external_ontology.get_annotation(term_iri, "http://www.w3.org/2000/01/rdf-schema#label")
                ext_definition = external_ontology.get_annotation(term_iri,
                                                                  "http://purl.obolibrary.org/obo/IAO_0000115")
                if ext_definition is None:
                    ext_definition = external_ontology.get_annotation(term_iri,
                                                                      "http://purl.obolibrary.org/obo/IAO_0000600")
                if ext_definition is None:
                    ext_definition = "no definition provided for external entity"
                    result.warning(type='external-no-definition',
                                   msg=f"No definition was provided for the external entity '{ext_label}' ({term_id}). Using default instead.")
                ext_parents = external_ontology.get_superclasses(term_iri)
                # If multiple parents check if they are (immediate) subclasses of each other and only take the most
                # specific parent.
                ext_parents -= set().union(*[external_ontology.get_superclasses(i) for i in ext_parents])
                ext_parents = [TermIdentifier(id=external_ontology.get_id_for_iri(cls)) for cls in ext_parents]

                if len(ext_parents) == 0:
                    self._logger.warning(f"External term has no parents: {term_id}")
                    continue

                ext_relations = [
                    (TermIdentifier("IAO:0000115", "definition"), ext_definition),
                    (TermIdentifier("IAO:0000114", "has curation status"), "External")
                ]
                ext_term = Term(term_id, ext_label, ("<external>", -1), ext_relations, ext_parents, [], [])

                r = self._api_client.declare_term(ext_term)
                if r.value == ():
                    # not created - TESTING ONLY
                    queue.append(ext_term)

                total += 1

        for term in ontology.terms():
            step += 1
            if update_fn:
                update_fn(step, total, f"Declare '{term.label}' ({term.id})")

            if term.curation_status() == "Obsolete":
                self._logger.info(f"Skipping obsolete term '{term.label}'")
            else:
                self._api_client.declare_term(term)

                queue.append(term)
                total += 1

        for term in queue:
            step += 1
            if update_fn:
                update_fn(step, total, f"Create '{term.label}' ({term.id})")

            try:
                self._api_client.update_term(term, revision_message)
            except HTTPError as e:
                result.error(type='http-error',
                             details=str(e),
                             response=e.response.json())

        result.value = ()
        return result
