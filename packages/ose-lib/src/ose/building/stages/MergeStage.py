from datetime import datetime
from typing import Callable, Literal

from ose.utils.asyncio import check_cancelled

from ose.building.Progress import Progress


from ose.result import ResultContext, with_result_context_method
from ose.building.HornedOntologyBuildService import HornedOntologyBuildService
from ose.building.stages.BuildStage import BuildStage
from ose.building.Progress import ProgressManager

EntityType = Literal["class", "object property", "data_property"]


class MergeStage(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "MERGE"

    @property
    def included_files(self) -> list[str]:
        return self.config.args.get("files", [])

    @with_result_context_method
    async def run(
        self, ctx: ResultContext, on_progress_update: Callable[[Progress], None] | None = None
    ) -> tuple[()]:
        progress = ProgressManager(on_progress_update)
        build_service = HornedOntologyBuildService()

        merge_files = [
            (n, f)
            for n, f in self.project.files.items()
            if all(s.type == "owl" for s in f.sources)
            and (n in self.included_files or f.target.publish)
        ]
        collapse_imports = [
            (n, f)
            for n, f in self.project.files.items()
            if (n in self.included_files or f.target.publish) and (n, f) not in merge_files
        ]

        progress.total_items = len(merge_files) + len(collapse_imports)

        for k, file in merge_files:
            progress.next_item(item=file.target.file, message="Collecting")

            ontologies = [
                self._local_name(n.file)
                for n in file.sources
                if n.file.endswith(".owl")
            ]
            version_iri = (
                file.target.iri + "/" + datetime.now().astimezone().strftime("%Y-%m-%d")
            )
                
            ctx.unwrap(await build_service.merge_ontologies(
                ontologies,
                self._local_name(file.target.file),
                file.target.iri,
                version_iri,
                file.target.ontology_annotations,
            ))

            self.context.add_final_artifact(file, self.name())

            await check_cancelled()

        for k, file in collapse_imports:
            progress.next_item(
                item=file.target.file, message="Collapsing import closure of"
            )

            out_file = self._local_name(file.target.file)

            ontologies = [self._local_name(file.target.file)]
            version_iri = (
                file.target.iri + "/" + datetime.now().astimezone().strftime("%Y-%m-%d")
            )
            ctx.unwrap(await build_service.merge_ontologies(
                ontologies,
                out_file,
                file.target.iri,
                version_iri,
                file.target.ontology_annotations,
            ))

            self.context.add_final_artifact(file, self.name())

            await check_cancelled()
        return ()
