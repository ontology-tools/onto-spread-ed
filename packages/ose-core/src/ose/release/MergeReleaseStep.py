from datetime import datetime
from typing import List, Optional

from .ReleaseContext import ReleaseContext
from .ReleaseStep import ReleaseStep
from ..model.Result import Result
from ..services.RobotOntologyBuildService import RobotOntologyBuildService


class MergeReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "MERGE"

    def __init__(self, context: ReleaseContext, *, files: Optional[List[str]] = None) -> None:
        super().__init__(context)

        if files is None:
            files = []
        self._files = files

    def run(self) -> bool:
        builder = RobotOntologyBuildService()
        result = Result(())

        merge_files = [(n, f) for n, f in self._release_script.files.items() if
                       all(s.type == "owl" for s in f.sources) and (n in self._files or f.target.publish)]
        collapse_imports = [(n, f) for n, f in self._release_script.files.items() if
                            (n in self._files or f.target.publish) and (n, f) not in merge_files]

        self._total_items = len(merge_files) + len(collapse_imports)

        for k, file in merge_files:
            self._next_item(item=file.target.file, message="Collecting")

            ontologies = [self._local_name(n.file) for n in file.sources if n.file.endswith(".owl")]
            version_iri = file.target.iri + "/" + datetime.utcnow().strftime("%Y-%m-%d")
            result += builder.merge_ontologies(ontologies, self._local_name(file.target.file), file.target.iri,
                                               version_iri,
                                               file.target.ontology_annotations)

            self._store_target_artifact(file)

            self._raise_if_canceled()

        for k, file in collapse_imports:
            self._next_item(item=file.target.file, message="Collapsing import closure of")

            [name, ext] = self._local_name(file.target.file).rsplit(".", 1)
            out_file = f"{name}.collapsed.{ext}"

            ontologies = [self._local_name(file.target.file)]
            version_iri = file.target.iri + "/" + datetime.utcnow().strftime("%Y-%m-%d")
            result += builder.merge_ontologies(ontologies, out_file, file.target.iri,
                                               version_iri,
                                               file.target.ontology_annotations)

            self._store_artifact(out_file, file.target.file)

            self._raise_if_canceled()

        self._set_release_result(result)
        return result.ok()
