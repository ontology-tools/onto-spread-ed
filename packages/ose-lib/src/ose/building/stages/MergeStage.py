from datetime import datetime, timezone
from typing import Callable, Literal

from ose.utils.asyncio import check_cancelled

from ose.building.Progress import Progress


from ose.result import Result, ResultContext
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
        return self.step_config.args.get("files", [])

    async def run(
        self, on_progress_update: Callable[[Progress], None] | None = None
    ) -> Result[tuple[()]]:
        with ResultContext() as log:
            progress = ProgressManager(on_progress_update)
            builder = HornedOntologyBuildService()

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

                [name, ext] = self._local_name(file.target.file).rsplit(".", 1)
                out_file = f"{name}.with-imports.{ext}"
                
                ontologies = [
                    self._local_name(n.file)
                    for n in file.sources
                    if n.file.endswith(".owl")
                ]
                version_iri = (
                    file.target.iri + "/" + datetime.utcnow().strftime("%Y-%m-%d")
                )
                
                log += await builder.merge_ontologies(
                    ontologies,
                    self._local_name(file.target.file),
                    file.target.iri,
                    version_iri,
                    file.target.ontology_annotations,
                )

                self.context._add_intermediate_artifact(out_file, type(self).__name__)

                await check_cancelled()

            for k, file in collapse_imports:
                progress.next_item(
                    item=file.target.file, message="Collapsing import closure of"
                )

                out_file = self._local_name(file.target.file)

                ontologies = [self._local_name(file.target.file)]
                version_iri = (
                    file.target.iri + "/" + datetime.now().astimezone(timezone.utc).strftime("%Y-%m-%d")
                )
                log += await builder.merge_ontologies(
                    ontologies,
                    out_file,
                    file.target.iri,
                    version_iri,
                    file.target.ontology_annotations,
                )

                self.context._add_final_artifact(file, type(self).__name__)

                await check_cancelled()
        return log.to_result()
