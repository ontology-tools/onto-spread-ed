import graphlib
from typing import Callable

from ose.utils.asyncio import check_cancelled

from ose.building.stages.BuildStage import BuildStage
from ose.result import Result, ResultContext, is_successful
from ose.ontology.ExcelOntology import ExcelOntology

from ose.building.RobotOntologyBuildService import RobotOntologyBuildService
from ose.building.Progress import Progress, ProgressManager


class ConversionStage(BuildStage):

    @classmethod
    def name(cls) -> str:
        return "EXCEL2OWL"

    async def run(
        self, on_progress_update: Callable[[Progress], None] | None = None
    ) -> Result[tuple[()]]:
        with ResultContext() as log:
            progress = ProgressManager(on_progress_update)

            builder = RobotOntologyBuildService()

            ts = graphlib.TopologicalSorter(
                {name: f.needs for name, f in self.project.files.items()}
            )
            sources = [(name, self.project.files[name]) for name in ts.static_order()]

            progress.total_items = len(sources)

            external_ontology_result = ExcelOntology.from_owl(
                self.project.external.target.file, self.project.prefixes
            )

            log += external_ontology_result.log
            if not is_successful(external_ontology_result):
                return log.fail()

            loaded: dict[str, ExcelOntology] = dict()
            for i, (k, file) in enumerate(sources):
                progress.next_item(item=file.target.file, message="Building")
                ontology = ExcelOntology(file.target.iri)

                await check_cancelled()

                external_ontology = external_ontology_result.value

                ontology.import_other_excel_ontology(external_ontology)

                await check_cancelled()

                for n in file.needs:
                    other = loaded[
                        n
                    ]  # Must exist queue is ordered to first load ontologies others depend on
                    log += ontology.import_other_excel_ontology(other)

                    await check_cancelled()

                for s in file.sources:
                    if s.type == "classes":
                        log += ontology.add_terms_from_excel(
                            s.file, self._local_name(s.file)
                        )
                    elif s.type == "relations":
                        log += ontology.add_relations_from_excel(
                            s.file, self._local_name(s.file)
                        )

                if file.renameTermFile is not None:
                    ontology.apply_renamings(self._local_name(file.renameTermFile))

                if file.addParentsFile is not None:
                    ontology.apply_new_parents(self._local_name(file.addParentsFile))

                log += ontology.resolve()
                await check_cancelled()

                dependencies = [
                    f
                    for f in (
                        [self.project.files[n].target.iri for n in file.needs]
                        + [self.project.external.target.iri]
                    )
                ]

                log += await builder.build_ontology(
                    ontology,
                    self._local_name(file.target.file),
                    self.project.prefixes,
                    dependencies,
                    self.context.project_dir,
                    self.project.iri_prefix,
                )

                self.context._add_intermediate_artifact(file, type(self).__name__)

                await check_cancelled()

                loaded[k] = ontology

        return log.to_result()
