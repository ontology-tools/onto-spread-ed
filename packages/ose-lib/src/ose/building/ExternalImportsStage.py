import csv
from typing import Callable, Tuple, List, Literal, cast

from ..utils.asyncio import check_cancelled

from .BuildStage import Progress


from ..excel_ontology.ExcelOntology import ExcelOntology
from ..model.Result import Result, ResultContext
from ..services.RobotOntologyBuildService import RobotOntologyBuildService
from .BuildStage import BuildStage

EntityType = Literal["class", "object property", "data_property"]


class ExternalImportsStage(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "EXTERNAL_IMPORTS"

    async def run(
        self, on_progress_update: Callable[[Progress], None] | None = None
    ) -> Result[tuple[()]]:
        with ResultContext() as log:
            file = self.project.external

            builder = RobotOntologyBuildService()

            ontology = ExcelOntology(file.target.iri)
            for s in file.sources:
                xlsx = self._local_name(s.file)
                log += ontology.add_imported_terms(s.file, xlsx)

                await check_cancelled()

            new_parents: List[Tuple[str, str, EntityType]] = []
            if file.addParentsFile:
                with open(self._local_name(file.addParentsFile)) as f:
                    rows = csv.DictReader(f, skipinitialspace=True)
                    for row in rows:
                        # Skip potential ROBOT header
                        if row.get("ID") == "ID":
                            continue

                        id = row.get("ID")
                        new_parent = row.get("NEW PARENT ID")
                        typ = cast(EntityType, row.get("TYPE", "class").lower())
                        if typ not in ["class", "object property", "data property"]:
                            log.warning(
                                type="unknown-owl-type",
                                file=file.renameTermFile,
                                msg=f"Unknown OWL type '{typ}' in column 'TYPE'",
                            )

                        if id is None or new_parent is None:
                            log.error(
                                type="invalid-add-parents-entry",
                                file=file.addParentsFile,
                                msg="Missing ID or NEW PARENT ID in add parents file",
                            )
                            continue

                        new_parents.append((id, new_parent, typ))

            renamings: List[Tuple[str, str, EntityType]] = []
            if file.renameTermFile is not None:
                with open(self._local_name(file.renameTermFile)) as f:
                    rows = csv.DictReader(f, skipinitialspace=True)
                    for row in rows:
                        # Skip potential ROBOT header
                        if row.get("ID") == "ID":
                            continue

                        id = row.get("ID")
                        new_label = row.get("NEW LABEL")
                        typ = cast(EntityType, row.get("TYPE", "class").lower())
                        if typ not in ["class", "object property", "data property"]:
                            log.warning(
                                type="unknown-owl-type",
                                file=file.renameTermFile,
                                msg=f"Unknown OWL type '{typ}' in column 'TYPE'",
                            )
                            typ = "class"

                        if id is None or new_label is None:
                            log.error(
                                type="invalid-rename-entry",
                                file=file.renameTermFile,
                                msg="Missing ID or NEW LABEL in rename file",
                            )
                            continue

                        renamings.append((id, new_label, typ))

            log += builder.merge_imports(
                ontology.imports(),
                self._local_name(file.target.file),
                file.target.iri,
                self.project.short_repository_name,
                self.context.project_dir,
                renamings,
                new_parents,
            )

            await check_cancelled()

            self.context._add_final_artifact(file, type(self).__name__)

        return log.to_result()
