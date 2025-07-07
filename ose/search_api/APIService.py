import abc
import asyncio
import logging
from typing import List, Callable, Optional, Tuple

import pyhornedowl

from ose.services.ConfigurationService import ConfigurationService
from .APIClient import APIClient
from .HttpError import HttpError
from ..model.ExcelOntology import ExcelOntology
from ..model.Result import Result
from ..model.Term import Term
from ..model.TermIdentifier import TermIdentifier
from ..utils import lower


class APIService(abc.ABC):
    _config: ConfigurationService
    _logger: logging.Logger
    _api_client: APIClient

    def __init__(self, config: ConfigurationService, api_client: APIClient):
        self._config = config
        self._api_client = api_client

    @property
    @abc.abstractmethod
    def repository_name(self) -> str:
        ...

    async def update_api(self, ontology: ExcelOntology,
                         external_ontologies: List[str],
                         revision_message: str,
                         update_fn: Optional[Callable[[int, int, str], None]] = None) -> Result[Tuple]:
        self._logger.info("Starting update")
        result = Result()

        config = self._config.get(self.repository_name)

        if config is None:
            self._logger.error(f"No config for repository '{self.repository_name}'!")

        external_ontologies_loaded = []
        for external in external_ontologies:
            ext_ontology = pyhornedowl.open_ontology(external)

            for (prefix, iri) in config.prefixes.items():
                ext_ontology.prefix_mapping.add_prefix(prefix, iri)

            external_ontologies_loaded.append(ext_ontology)

        external_classes = [(o, o.get_classes()) for o in external_ontologies_loaded]
        total = sum(len(classes) for o, classes in external_classes) + len(ontology.terms())
        step = 0

        queue: List[Term] = []

        # edit lock for modifying the queue or counters
        lock = asyncio.Lock()

        # Only allow 5 concurrent calls to the API
        sem = asyncio.Semaphore(5)

        async def handle_external(o: pyhornedowl.PyIndexedOntology, term_iri: str):
            nonlocal step, total
            async with sem:
                async with lock:
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
                                       msg="No definition was provided for the external " +
                                           f"entity '{ext_label}' ({term_id}). Using default instead.")

                    if ext_label is None:
                        result.warning(type="external-no-label",
                                       msg=f"The external term \"{term_id}\" has no label. Skipping it")
                        return

                    ext_parents = o.get_superclasses(term_iri)
                    # If multiple parents check if they are (immediate) subclasses of each other and only take the most
                    # specific parent.
                    ext_parents -= set().union(*[o.get_ancestors(i) for i in ext_parents])
                    ext_parents = [TermIdentifier(id=o.get_id_for_iri(cls)) for cls in ext_parents]
                    ext_parents = [p for p in ext_parents if p.id is not None]

                    if len(ext_parents) == 0:
                        self._logger.warning(f"External term has no parents: {term_id}")
                        return
                    if len(ext_parents) > 1:
                        self._logger.warning(f"Multiple parents defined for external term: {term_id}."
                                             "Using only the lexicographical first entry.")
                        ext_parents = [sorted(ext_parents)[0]]

                    ext_relations = [
                        (TermIdentifier("IAO:0000115", "definition"), ext_definition),
                        (TermIdentifier("IAO:0000114", "has curation status"), "External")
                    ]
                    ext_term = Term(term_id, ext_label, ("<external>", -1), ext_relations, ext_parents, [], [])

                    await self._api_client.declare_term(ext_term)

                    async with lock:
                        queue.append(ext_term)
                        total += 1
                else:
                    await self._api_client.declare_term(term)

                    async with lock:
                        queue.append(term)
                        total += 1

        tasks = [handle_external(o, term_iri) for o, classes in external_classes for term_iri in classes]
        await asyncio.gather(*tasks)

        async def declare_term(term: Term):
            nonlocal step, total
            async with sem:
                async with lock:
                    step += 1

                    if update_fn:
                        update_fn(step, total, f"declaring '{term.label}' ({term.id})")

                if lower(term.curation_status()) in ["obsolete", "pre-proposed"]:
                    self._logger.info(f"Skipping {term.curation_status()} term '{term.label}'")
                else:
                    await self._api_client.declare_term(term)

                    async with lock:
                        queue.append(term)
                        total += 1

        tasks = [declare_term(term) for term in ontology.terms()]
        await asyncio.gather(*tasks)

        async def work_queue(term: Term):
            nonlocal step, total
            async with sem:
                async with lock:
                    step += 1

                    if update_fn:
                        update_fn(step, total, f"updating '{term.label}' ({term.id})")

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

    async def get_all_terms(self) -> List[Term]:
        next_page = 1
        items = []

        while next_page is not None:
            page = await self._api_client.get_terms(next_page)

            items.extend(page.items)
            next_page = page.next_page

        return items
