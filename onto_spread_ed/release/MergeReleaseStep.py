from datetime import datetime

from .ReleaseStep import ReleaseStep
from .common import order_sources
from ..model.Result import Result
from ..services.RobotOntologyBuildService import RobotOntologyBuildService


class MergeReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "MERGE"

    def run(self) -> bool:
        builder = RobotOntologyBuildService()
        result = Result(())

        files = [(n, f) for n, f in self._release_script.files.items() if all(s.type == "owl" for s in f.sources)]

        for k, file in files:
            ontologies = [self._local_name(n.file) for n in file.sources if n.file.endswith(".owl")]
            version_iri = file.target.iri + "/" + datetime.utcnow().strftime("%Y-%m-%d")
            result += builder.merge_ontologies(ontologies, self._local_name(file.target.file), file.target.iri, version_iri,
                                               file.target.ontology_annotations)

            self._raise_if_canceled()

        self._set_release_result(result)
        return result.ok()
