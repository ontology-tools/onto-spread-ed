import asyncio
import logging
import os
from typing import List, Callable, Optional, Tuple

import aiohttp
import pyhornedowl
import requests
from requests import HTTPError

from .APIService import APIService
from .BCIOSearchClient import BCIOSearchClient
from .HttpError import HttpError
from ..model.ExcelOntology import ExcelOntology
from ..model.Result import Result
from ..model.Term import Term
from ..model.TermIdentifier import TermIdentifier

PROP_BCIO_SEARCH_API_PATH = "BCIO_SEARCH_API_PATH"
PROP_BCIO_SEARCH_API_AUTH_TOKEN = "BCIO_SEARCH_API_AUTH_TOKEN"


class BCIOSearchService(APIService):
    _api_client: BCIOSearchClient
    _logger = logging.getLogger(__name__)

    def __init__(self, config: dict, session: aiohttp.ClientSession):
        super().__init__(config)

        path = config.get(PROP_BCIO_SEARCH_API_PATH)
        authtoken = config.get(PROP_BCIO_SEARCH_API_AUTH_TOKEN, os.environ.get(PROP_BCIO_SEARCH_API_AUTH_TOKEN, None))

        self._config = config

        self._api_client = BCIOSearchClient(path, session, authtoken, config.get("DEBUG", False))

        self._logger.addHandler(logging.FileHandler("logs/release_bcio_search.log"))

    async def update_api(self, ontology: ExcelOntology,
                         external_ontologies: List[str],
                         revision_message: str,
                         update_fn: Optional[Callable[[int, int, str], None]] = None) -> Result[Tuple]:

        self._logger.info("Starting update")
        result = Result()

        external_ontologies_loaded = []
        for external in external_ontologies:
            ext_ontology = pyhornedowl.open_ontology(external)

            for [prefix, iri] in self._config["PREFIXES"]:
                ext_ontology.add_prefix_mapping(prefix, iri)

            external_ontologies_loaded.append(ext_ontology)

        external_classes = [(o, o.get_classes()) for o in external_ontologies_loaded]
        total = len(external_classes) + len(ontology.terms())
        step = 0

        queue: List[Term] = []

        # Only allow 5 concurrent calls to the API
        sem = asyncio.Semaphore(5)

        async def handle_external(o: pyhornedowl.PyIndexedOntology, term_iri: str):
            nonlocal step, total
            async with sem:
                step += 1
                if update_fn:
                    update_fn(step, total, f"External - {term_iri}")

                term_id = o.get_id_for_iri(term_iri)
                if term_id is None:
                    self._logger.warning(f"Term has no id {term_iri}")
                    return

                term = ontology.term_by_id(term_id)
                if term is None:
                    ext_label = o.get_annotation(term_iri, "http://www.w3.org/2000/01/rdf-schema#label")
                    ext_definition = o.get_annotation(term_iri,
                                                                      "http://purl.obolibrary.org/obo/IAO_0000115")
                    if ext_definition is None:
                        ext_definition = o.get_annotation(term_iri,
                                                                          "http://purl.obolibrary.org/obo/IAO_0000600")
                    if ext_definition is None:
                        ext_definition = "no definition provided for external entity"
                        result.warning(type='external-no-definition',
                                       msg=f"No definition was provided for the external entity '{ext_label}' ({term_id}). "
                                           f"Using default instead.")
                    ext_parents = o.get_superclasses(term_iri)
                    # If multiple parents check if they are (immediate) subclasses of each other and only take the most
                    # specific parent.
                    ext_parents -= set().union(*[o.get_superclasses(i) for i in ext_parents])
                    ext_parents = [TermIdentifier(id=o.get_id_for_iri(cls)) for cls in ext_parents]
                    ext_parents = [p for p in ext_parents if p.id is not None]

                    if len(ext_parents) == 0:
                        self._logger.warning(f"External term has no parents: {term_id}")
                        return

                    ext_relations = [
                        (TermIdentifier("IAO:0000115", "definition"), ext_definition),
                        (TermIdentifier("IAO:0000114", "has curation status"), "External")
                    ]
                    ext_term = Term(term_id, ext_label, ("<external>", -1), ext_relations, ext_parents, [], [])

                    await self._api_client.declare_term(ext_term)
                    queue.append(ext_term)

                    total += 1

        tasks = [handle_external(o, term_iri) for o, classes in external_classes for term_iri in classes]
        await asyncio.gather(*tasks)

        async def declare_term(term: Term):
            nonlocal step, total
            async with sem:
                step += 1
                if update_fn:
                    update_fn(step, total, f"Declare '{term.label}' ({term.id})")

                if term.curation_status() == "Obsolete":
                    self._logger.info(f"Skipping obsolete term '{term.label}'")
                else:
                    await self._api_client.declare_term(term)

                    queue.append(term)
                    total += 1

        tasks = [declare_term(term) for term in ontology.terms()]
        await asyncio.gather(*tasks)

        async def work_queue(term: Term):
            nonlocal step, total
            async with sem:
                step += 1
                if update_fn:
                    update_fn(step, total, f"Create '{term.label}' ({term.id})")

                try:
                    await self._api_client.update_term(term, revision_message)
                except HttpError as e:
                    result.error(type='http-error',
                                 details=e.message,
                                 response=e.response)

        tasks = [work_queue(term) for term in queue]
        await asyncio.gather(*tasks)

        result.value = ()
        return result
