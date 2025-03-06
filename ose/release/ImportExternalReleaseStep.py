import csv
from typing import Tuple, List, Literal

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy

from .ReleaseStep import ReleaseStep
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScript
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..services.RobotOntologyBuildService import RobotOntologyBuildService


class ImportExternalReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "IMPORT_EXTERNAL"

    def __init__(self, db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int, tmp: str,
                 config: ConfigurationService, *, use_existing_file: bool = False) -> None:
        super().__init__(db, gh, release_script, release_id, tmp, config)

        self._use_existing_file = use_existing_file

    def run(self) -> bool:
        result = Result(())
        file = self._release_script.external

        # If e.g. the external owl file is built automatically after each change we can use that file
        if self._use_existing_file:
            self._download(file.target.file)

            self.store_target_artifact(file, downloadable=False)

            self._set_release_result(result)
            return result.ok()

        builder = RobotOntologyBuildService()

        ontology = ExcelOntology(file.target.iri)
        for s in file.sources:
            xlsx = self._local_name(s.file)
            result += ontology.add_imported_terms(s.file, xlsx)

            self._raise_if_canceled()

        new_parents: List[Tuple[str, str, Literal["class", "object property", "data_property"]]] = []
        if file.addParentsFile:
            with open(self._local_name(file.addParentsFile)) as f:
                rows = csv.DictReader(f, skipinitialspace=True)
                for row in rows:
                    # Skip potential ROBOT header
                    if row.get("ID") == "ID":
                        continue

                    id = row.get("ID")
                    new_parent = row.get("NEW PARENT ID")
                    type = row.get("TYPE", "class").lower()
                    if type not in ["class", "object property", "data property"]:
                        result.warning(type='unknown-owl-type',
                                       file=file.renameTermFile,
                                       msg=f"Unknown OWL type '{type}' in column 'TYPE'")

                    new_parents.append((id, new_parent, type))

        renamings: List[Tuple[str, str, Literal["class", "object property", "data_property"]]] = []
        if file.renameTermFile is not None:
            with open(self._local_name(file.renameTermFile)) as f:
                rows = csv.DictReader(f, skipinitialspace=True)
                for row in rows:
                    # Skip potential ROBOT header
                    if row.get("ID") == "ID":
                        continue

                    id = row.get("ID")
                    new_label = row.get("NEW LABEL")
                    type = row.get("TYPE", "class").lower()
                    if type not in ["class", "object property", "data property"]:
                        result.warning(type='unknown-owl-type',
                                       file=file.renameTermFile,
                                       msg=f"Unknown OWL type '{type}' in column 'TYPE'")
                        type = "class"

                    renamings.append((id, new_label, type))

        result += builder.merge_imports(
            ontology.imports(),
            self._local_name(file.target.file),
            file.target.iri,
            self._release_script.short_repository_name,
            self._working_dir,
            renamings,
            new_parents
        )

        self._raise_if_canceled()

        self.store_target_artifact(file, downloadable=False)

        self._set_release_result(result)
        return result.ok()
