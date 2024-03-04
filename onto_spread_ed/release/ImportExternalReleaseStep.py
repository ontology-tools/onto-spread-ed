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

        ontology = ExcelOntology(self._release_script.external.target.iri)
        for s in self._release_script.external.sources:
            xlsx = self._local_name(s.file)
            result += ontology.add_imported_terms(s.file, xlsx)

            self._raise_if_canceled()

        result += builder.merge_imports(
            ontology.imports(),
            self._local_name(self._release_script.external.target.file),
            self._release_script.external.target.iri,
            self._release_script.short_repository_name,
            self._working_dir
        )
        self._raise_if_canceled()

        self._set_release_result(result)
        return result.ok()
