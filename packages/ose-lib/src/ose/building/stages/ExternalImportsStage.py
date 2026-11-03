import csv
from typing import Callable, Tuple, List, Literal, cast

from ose.utils.asyncio import check_cancelled

from ose.building.Progress import Progress


from ose.ontology.ExcelOntology import ExcelOntology
from ose.result import ResultContext, with_result_context_method
from ose.building.RobotOntologyBuildService import RobotOntologyBuildService
from ose.building.stages.BuildStage import BuildStage

EntityType = Literal["class", "object property", "data_property"]


class ExternalImportsStage(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "EXTERNAL_IMPORTS"

    @with_result_context_method
    def _read_csv(self, ctx: ResultContext, file: str) -> list[dict[str, str]]:
        try:
            with open(self._local_name(file)) as f:
                return list(csv.DictReader(f, skipinitialspace=True))
        except OSError as e:
            ctx.fail(type="unreadable-file", file=file, msg=str(e))

    @with_result_context_method
    async def run(
        self, ctx: ResultContext, on_progress_update: Callable[[Progress], None] | None = None
    ) -> tuple[()]:
        file = self.project.external

        build_service = RobotOntologyBuildService()

        ontology = ExcelOntology(file.target.iri)
        for s in file.sources:
            xlsx = self._local_name(s.file)
            ctx.unwrap(ontology.add_imported_terms(s.file, xlsx))

            await check_cancelled()

        new_parents: List[Tuple[str, str, EntityType]] = []
        if file.addParentsFile:
            rows = ctx.unwrap(self._read_csv(file.addParentsFile))
            for row in rows:
                # Skip potential ROBOT header
                if row.get("ID") == "ID":
                    continue

                id = row.get("ID")
                new_parent = row.get("NEW PARENT ID")
                typ = cast(EntityType, row.get("TYPE", "class").lower())
                if typ not in ["class", "object property", "data property"]:
                    ctx.log.warning(
                        type="unknown-owl-type",
                        file=file.addParentsFile,
                        msg=f"Unknown OWL type '{typ}' in column 'TYPE'",
                    )

                if id is None or new_parent is None:
                    ctx.log.error(
                        type="invalid-add-parents-entry",
                        file=file.addParentsFile,
                        msg="Missing ID or NEW PARENT ID in add parents file",
                    )
                    continue

                new_parents.append((id, new_parent, typ))

        renamings: List[Tuple[str, str, EntityType]] = []
        if file.renameTermFile is not None:
            rows = ctx.unwrap(self._read_csv(file.renameTermFile))
            for row in rows:
                # Skip potential ROBOT header
                if row.get("ID") == "ID":
                    continue

                id = row.get("ID")
                new_label = row.get("NEW LABEL")
                typ = cast(EntityType, row.get("TYPE", "class").lower())
                if typ not in ["class", "object property", "data property"]:
                    ctx.log.warning(
                        type="unknown-owl-type",
                        file=file.renameTermFile,
                        msg=f"Unknown OWL type '{typ}' in column 'TYPE'",
                    )
                    typ = "class"

                if id is None or new_label is None:
                    ctx.log.error(
                        type="invalid-rename-entry",
                        file=file.renameTermFile,
                        msg="Missing ID or NEW LABEL in rename file",
                    )
                    continue

                renamings.append((id, new_label, typ))

        if ctx.log.has_errors():
            ctx.fail()

        ctx.unwrap(await build_service.merge_imports(
            ontology.imports(),
            self._local_name(file.target.file),
            file.target.iri,
            self.project.short_repository_name,
            renamings,
            new_parents,
        ))

        await check_cancelled()

        self.context.add_final_artifact(file, self.name())

        return ()
