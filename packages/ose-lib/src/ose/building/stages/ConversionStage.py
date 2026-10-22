import graphlib
from typing import Callable

from ose.utils.asyncio import check_cancelled

from ose.building.stages.BuildStage import BuildStage
from ose.result import ResultContext, with_result_context_method
from ose.ontology.ExcelOntology import ExcelOntology

from ose.building.RobotOntologyBuildService import RobotOntologyBuildService
from ose.building.Progress import Progress, ProgressManager


class ConversionStage(BuildStage):

    @classmethod
    def name(cls) -> str:
        return "EXCEL2OWL"

    @with_result_context_method
    async def run(
        self,
        ctx: ResultContext,
        on_progress_update: Callable[[Progress], None] | None = None,
    ) -> tuple[()]:
        progress = ProgressManager(on_progress_update)

        builder = RobotOntologyBuildService()

        ts = graphlib.TopologicalSorter(
            {name: f.needs for name, f in self.project.files.items()}
        )
        sources = [(name, self.project.files[name]) for name in ts.static_order()]

        progress.total_items = len(sources)

        external_ontology = ctx.unwrap(
            ExcelOntology.from_owl(
                self._local_name(self.project.external.target.file),
                self.project.prefixes,
            )
        )

        loaded: dict[str, ExcelOntology] = dict()
        # IRIs of the ontologies of this build, mapped to their files
        local_ontologies = {
            self.project.external.target.iri: self._local_name(self.project.external.target.file)
        }
        for i, (k, file) in enumerate(sources):
            progress.next_item(item=file.target.file, message="Building")
            ontology = ExcelOntology(file.target.iri)

            await check_cancelled()

            ctx.unwrap(ontology.import_other_excel_ontology(external_ontology))

            await check_cancelled()

            for n in file.needs:
                other = loaded[
                    n
                ]  # Must exist queue is ordered to first load ontologies others depend on
                ctx.unwrap(ontology.import_other_excel_ontology(other))

                await check_cancelled()

            for s in file.sources:
                schema = self.project.spreadsheet_schema(s.spreadsheet_schema)
                if schema is None:
                    ctx.fail(
                        type="schema-not-found",
                        msg=f"Spreadsheet schema '{s.spreadsheet_schema}' not found.",
                    )

                if s.type == "classes":
                    ctx.unwrap(
                        ontology.add_terms_from_excel(s.file, self._local_name(s.file), schema)
                    )
                elif s.type == "relations":
                    ctx.unwrap(
                        ontology.add_relations_from_excel(
                            s.file, self._local_name(s.file), schema
                        )
                    )

            if file.renameTermFile is not None:
                ontology.apply_renamings(self._local_name(file.renameTermFile))

            if file.addParentsFile is not None:
                ontology.apply_new_parents(self._local_name(file.addParentsFile))

            ctx.unwrap(ontology.resolve())
            await check_cancelled()

            dependency_iris = [self.project.files[n].target.iri for n in file.needs] + [
                self.project.external.target.iri
            ]
            outfile = self._local_name(file.target.file)

            ctx.unwrap(
                await builder.build_ontology(
                    ontology,
                    outfile,
                    self.project.prefixes,
                    dependency_iris,
                    dict(local_ontologies),
                    self.project.iri_prefix,
                )
            )
            local_ontologies[file.target.iri] = outfile

            self.context.add_intermediate_artifact(file, self.name())

            await check_cancelled()

            loaded[k] = ontology

        return ()
