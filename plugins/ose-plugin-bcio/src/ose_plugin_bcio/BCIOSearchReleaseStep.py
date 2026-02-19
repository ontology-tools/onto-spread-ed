import asyncio
from datetime import datetime
from typing import List

import aiohttp

from ose.model.ExcelOntology import ExcelOntology
from ose.model.Result import Result
from ose.release.ReleaseContext import ReleaseContext
from ose.release.ReleaseStep import ReleaseStep
from ose.release.common import order_sources
from .BCIOSearchService import BCIOSearchService


class BCIOSearchReleaseStep(ReleaseStep):
    _included_files: List[str]

    @classmethod
    def name(cls) -> str:
        return "BCIO_SEARCH"

    @classmethod
    def accepts_context(cls, context: ReleaseContext) -> bool:
        return context.config_service is not None

    def __init__(self, context: ReleaseContext, *, included_files: List[str]):
        super().__init__(context)

        self._included_files = included_files

    def run(self) -> bool:
        result = Result()
        sources = order_sources(
            dict([(k, f) for k, f in self._release_script.files.items() if k in self._included_files])
        )

        ontology = ExcelOntology("")
        for s in self._release_script.external.sources:
            xlsx = self._local_name(s.file)
            result += ontology.add_imported_terms(s.file, xlsx)

        for i, (k, file) in enumerate(sources):
            for s in file.sources:
                if s.type == "classes":
                    result += ontology.add_terms_from_excel(s.file, self._local_name(s.file))
                elif s.type == "relations":
                    result += ontology.add_relations_from_excel(s.file, self._local_name(s.file))

                self._raise_if_canceled()

        ontology.resolve()
        self._raise_if_canceled()

        ontology.remove_duplicates()
        self._raise_if_canceled()

        externals = [self._local_name(self._release_script.external.target.file)]
        result += asyncio.run(self.run_service(ontology, externals))

        self._raise_if_canceled()

        self._set_release_result(result)
        return result.ok()

    async def run_service(self, ontology: ExcelOntology, externals: List[str]) -> Result[tuple]:
        config_service = self._context.config_service
        assert config_service is not None  # Guaranteed by accepts_context

        async with aiohttp.ClientSession() as session:
            service = BCIOSearchService(config_service, session)
            return await service.update_api(
                ontology,
                externals,
                f"{datetime.utcnow().strftime('%B %Y')} Release",
                lambda step, total, msg: self._update_progress(position=(step, total), current_item=msg),
            )
