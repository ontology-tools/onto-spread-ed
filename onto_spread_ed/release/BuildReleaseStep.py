import os.path

from .ReleaseStep import ReleaseStep
from .common import order_sources
from ..model.ExcelOntology import ExcelOntology
from ..model.Result import Result
from ..services.RobotOntologyBuildService import RobotOntologyBuildService


class BuildReleaseStep(ReleaseStep):
    def run(self) -> bool:
        result = Result(())
        builder = RobotOntologyBuildService()
        sources = order_sources(self._release_script.files)

        self._total_items = len(sources)

        loaded = dict()
        for i, (k, file) in enumerate(sources):
            self._next_item()
            ontology = ExcelOntology(file.target.iri)

            for s in self._release_script.external.sources:
                xlsx = self._local_name(s.file)
                result += ontology.add_imported_terms(s.file, xlsx)

                self._raise_if_canceled()

            for n in file.needs:
                other = loaded[n]  # Must exist queue is ordered to first load ontologies others depend on
                result += ontology.import_other_excel_ontology(other)

                self._raise_if_canceled()

            for s in file.sources:
                if s.type == "classes":
                    result += ontology.add_terms_from_excel(s.file, self._local_name(s.file))
                elif s.type == "relations":
                    result += ontology.add_relations_from_excel(s.file, self._local_name(s.file))

            result += ontology.resolve()
            self._raise_if_canceled()

            result += builder.build_ontology(ontology, self._local_name(file.target.file), self._release_script.prefixes, [
                os.path.basename(f) for f in ([self._release_script.files[n].target.file for n in file.needs] + [self._release_script.external.target.file])
            ], self._working_dir)
            self._raise_if_canceled()

            loaded[k] = ontology

        result.warnings = []
        self._set_release_result(result)
        return result.ok()

    # result, upper = _load_upper()
    # _raise_if_canceled()
    #
    # total = len(release.included_files)
    # for index, f in enumerate(release.included_files):
    #
    #     result += onto.add_terms_from_excel(f, _local_name(f))
    #     result += onto.resolve()
    #     _raise_if_canceled()
    #
    #     result += builder.build_ontology(onto, _local_name(f, ".owl"), release_script.prefixes, [
    #         os.path.basename(release_script.external[1]),
    #         os.path.basename(release_script.upper_level[1])
    #     ], tmp)
    #     _raise_if_canceled()
    #
    # result.warnings = []
    # set_release_result(q, release_id, result)
    # return result.ok()

    @classmethod
    def name(cls) -> str:
        return "BUILD"
