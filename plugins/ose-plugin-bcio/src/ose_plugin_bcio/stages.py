from datetime import datetime, timezone
from graphlib import TopologicalSorter

import aiohttp

from ose.building.stages import BuildStage
from ose.building.Progress import ProgressManager
from ose.ontology import ExcelOntology
from ose.result import ResultContext, with_result_context_method
from ose.utils.asyncio import check_cancelled
from .BCIOSearchService import BCIOSearchService


class BCIOSearchStage(BuildStage):
    def __init__(self, step_config, context):
        super().__init__(step_config, context)
        self._included_files = self.config.args["included_files"]

    @classmethod
    def name(cls) -> str:
        return "BCIO_SEARCH"

    @with_result_context_method
    async def run(self, ctx: ResultContext, on_progress_update=None):
        files = {key: file for key, file in self.project.files.items() if key in self._included_files}
        order = TopologicalSorter({key: [n for n in file.needs if n in files] for key, file in files.items()})
        ontology = ExcelOntology("")
        progress = ProgressManager(on_progress_update)
        for source in self.project.external.sources:
            await check_cancelled()
            ctx.unwrap(ontology.add_imported_terms(source.file, self._local_name(source.file)))
        for key in order.static_order():
            for source in files[key].sources:
                await check_cancelled()
                progress.next_item(item=source.file, message="Loading ontology")
                if source.type == "classes":
                    ctx.unwrap(ontology.add_terms_from_excel(source.file, self._local_name(source.file)))
                elif source.type == "relations":
                    ctx.unwrap(ontology.add_relations_from_excel(source.file, self._local_name(source.file)))
        ctx.unwrap(ontology.resolve())
        ontology.remove_duplicates()
        await check_cancelled()
        def update(step, total, message):
            progress.total_items = total
            progress.current_item = step - 2
            progress.next_item(item=message)
        async with aiohttp.ClientSession() as session:
            service = BCIOSearchService(self.project.prefixes, session)
            result = await service.update_api(
                ontology, [self._local_name(self.project.external.target.file)],
                f"{datetime.now(timezone.utc).strftime('%B %Y')} Release", update,
            )
        self.result_data["errors"] = result.log.errors
        ctx.unwrap(result)
        await check_cancelled()
        return self.result_data
