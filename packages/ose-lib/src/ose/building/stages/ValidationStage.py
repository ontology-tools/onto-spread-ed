import graphlib
from typing import Callable

from ose.utils.asyncio import check_cancelled

from ose.building.stages.BuildStage import BuildStage, StageResult
from ose.building.Progress import Progress, ProgressManager
from ose.project import ProjectFile
from ose.result import ResultContext, with_result_context_method
from ose.ontology import ExcelOntology


class ValidationStage(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "VALIDATION"

    @with_result_context_method
    async def run(
        self, ctx: ResultContext, on_progress_update: Callable[[Progress], None] | None = None
    ) -> StageResult:
        validation_info = self.result_data
        progress = ProgressManager(on_progress_update)

        ts = graphlib.TopologicalSorter({name: f.needs for name, f in self.project.files.items()})
        sources = [(name, self.project.files[name]) for name in ts.static_order()]

        external = ctx.unwrap(
            ExcelOntology.from_owl(self._local_name(self.project.external.target.file), self.project.prefixes)
        )
        await check_cancelled()

        # To catch overarching errors
        overall_ontology = ExcelOntology("<final>")
        ctx.unwrap(overall_ontology.import_other_excel_ontology(external))

        loaded: dict[str, ExcelOntology] = dict()
        for k, file in sources:
            progress.next_item(item=k, message="Validating")

            if all(s.type == "owl" for s in file.sources):
                continue

            result = await self._validate_file(file, external, loaded)
            validation_info[k] = dict(
                valid=result.successful,
                warnings=result.log.warnings,
                errors=result.log.errors,
            )

            if (ontology := ctx.attempt(result)) is not None:
                overall_ontology.merge_with(ontology)
                loaded[k] = ontology

        only = self.config.args.get("only")
        global_result = overall_ontology.validate(
            only=["duplicate"] if only is None or "duplicate" in only else [],
            exclude=self.config.args.get("exclude"),
        )
        validation_info["global"] = dict(
            valid=global_result.successful,
            warnings=global_result.log.warnings,
            errors=global_result.log.errors,
        )
        ctx.attempt(global_result)

        return validation_info

    @with_result_context_method
    async def _validate_file(
        self, ctx: ResultContext, file: ProjectFile, external: ExcelOntology, loaded: dict[str, ExcelOntology]
    ) -> ExcelOntology:
        ontology = ExcelOntology(file.target.iri)
        ctx.unwrap(ontology.import_other_excel_ontology(external))

        await check_cancelled()

        for n in file.needs:
            if n not in loaded:
                ctx.fail(type="dependency-failed", file=file.target.file, msg=f"Depends on '{n}', which failed")

            ctx.unwrap(
                ontology.import_other_excel_ontology(loaded[n])
            )  # Must exist queue is ordered to first load ontologies others depend on

            await check_cancelled()

        for s in file.sources:
            schema = self.project.spreadsheet_schema(s.spreadsheet_schema)
            if s.type == "classes":
                ctx.unwrap(ontology.add_terms_from_excel(s.file, self._local_name(s.file), schema))
            elif s.type == "relations":
                ctx.unwrap(ontology.add_relations_from_excel(s.file, self._local_name(s.file), schema))
            elif s.type == "owl":
                imported = ctx.unwrap(ExcelOntology.from_owl(self._local_name(s.file), self.project.prefixes))
                ctx.unwrap(ontology.import_other_excel_ontology(imported))
            else:
                ctx.fail(type="not-implemented", msg=f"Source type '{s.type}' is not implemented yet.")

            await check_cancelled()

        if file.renameTermFile is not None:
            ontology.apply_renamings(self._local_name(file.renameTermFile))

        if file.addParentsFile is not None:
            ontology.apply_new_parents(self._local_name(file.addParentsFile))

        ctx.unwrap(ontology.resolve())
        await check_cancelled()

        ctx.unwrap(ontology.validate(only=self.config.args.get("only"), exclude=self.config.args.get("exclude")))
        await check_cancelled()

        return ontology
