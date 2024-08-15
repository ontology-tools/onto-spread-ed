import csv
from typing import Tuple, List

from .ReleaseStep import ReleaseStep
from ..model.ExcelOntology import ExcelOntology
from ..model.Result import Result
from ..services.RobotOntologyBuildService import RobotOntologyBuildService


class ImportExternalReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "IMPORT_EXTERNAL"

    def run(self) -> bool:
        builder = RobotOntologyBuildService()

        result = Result(())

        file = self._release_script.external
        ontology = ExcelOntology(file.target.iri)
        for s in file.sources:
            xlsx = self._local_name(s.file)
            result += ontology.add_imported_terms(s.file, xlsx)

            self._raise_if_canceled()

        new_parents: List[Tuple[str, str]] = []
        if file.addParentsFile:
            with open(self._local_name(file.addParentsFile)) as f:
                rows = csv.reader(f)
                next(rows)

                for row in rows:
                    # Skip potential ROBOT header
                    if row[0] == "ID" or len(row) < 2:
                        continue

                    new_parents.append((row[0], row[1]))

        renamings: List[Tuple[str, str]] = []
        if file.renameTermFile is not None:
            with open(self._local_name(file.renameTermFile)) as f:
                rows = csv.reader(f)
                next(rows)

                for row in rows:
                    # Skip potential ROBOT header
                    if row[0] == "ID" or len(row) < 2:
                        continue

                    renamings.append((row[0], row[1]))

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

        self._set_release_result(result)
        return result.ok()
