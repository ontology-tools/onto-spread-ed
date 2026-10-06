import graphlib
from typing import Callable

from ose.utils.asyncio import check_cancelled

from ose.building.stages.BuildStage import BuildStage, StageResult
from ose.building.Progress import Progress, ProgressManager
from ose.result import Result, ResultContext, is_successful
from ose.ontology import ExcelOntology



class ValidationStage(BuildStage):

    @classmethod
    def name(cls) -> str:
        return "VALIDATION"

    async def run(
        self, on_progress_update: Callable[[Progress], None] | None = None
    ) -> Result[StageResult]:
        with ResultContext() as log:
            validation_info = dict()
            progress = ProgressManager(on_progress_update)

            ts = graphlib.TopologicalSorter(
                {name: f.needs for name, f in self.project.files.items()}
            )
            sources = [(name, self.project.files[name]) for name in ts.static_order()]

            external_ontology_result = ExcelOntology.from_owl(
                self._local_name(self.project.external.target.file), self.project.prefixes
            )

            log += external_ontology_result.log
            if not is_successful(external_ontology_result):
                return log.fail()

            external = external_ontology_result.value
            await check_cancelled()

            # To catch overarching errors
            overall_ontology = ExcelOntology("<final>")
            overall_ontology.import_other_excel_ontology(external)

            loaded: dict[str, ExcelOntology] = dict()
            for k, file in sources:
                progress.next_item(item=k, message="Validating")

                ontology = ExcelOntology(file.target.iri)
                ontology.import_other_excel_ontology(external)

                await check_cancelled()

                with ResultContext() as validation_log:
                    for n in file.needs:
                        other = loaded[
                            n
                        ]  # Must exist queue is ordered to first load ontologies others depend on
                        validation_log += ontology.import_other_excel_ontology(other)

                        await check_cancelled()

                    for s in file.sources:
                        if s.type == "classes":
                            validation_log += ontology.add_terms_from_excel(
                                s.file, self._local_name(s.file)
                            )
                        elif s.type == "relations":
                            validation_log += ontology.add_relations_from_excel(
                                s.file, self._local_name(s.file)
                            )

                        await check_cancelled()

                    if file.renameTermFile is not None:
                        ontology.apply_renamings(self._local_name(file.renameTermFile))

                    if file.addParentsFile is not None:
                        ontology.apply_new_parents(
                            self._local_name(file.addParentsFile)
                        )

                    validation_log += ontology.resolve()
                    await check_cancelled()

                    validation_log += ontology.validate()
                    await check_cancelled()

                    validation_info[k] = dict(
                        valid=not validation_log.has_errors(),
                        warnings=validation_log.warnings,
                        errors=validation_log.errors,
                    )

                    overall_ontology.merge_with(ontology)
                    loaded[k] = ontology

                log += validation_log

            result = overall_ontology.validate(only=["duplicate"])
            validation_info["global"] = dict(
                valid=not result.log.has_errors(),
                warnings=result.log.warnings,
                errors=result.log.errors,
            )
            log += result

        return log.to_result(validation_info)
