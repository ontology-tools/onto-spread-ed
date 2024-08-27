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

            external_ontology_result = self.load_externals_ontology()

            self._raise_if_canceled()

            result += external_ontology_result
            ontology.import_other_excel_ontology(external_ontology_result.value)

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

            if file.renameTermFile is not None:
                ontology.apply_renamings(self._local_name(file.renameTermFile))

            if file.addParentsFile is not None:
                ontology.apply_new_parents(self._local_name(file.addParentsFile))

            result += ontology.resolve()
            self._raise_if_canceled()

            dependencies = [f for f in (
                    [self._release_script.files[n].target.iri for n in file.needs] +
                    [self._release_script.external.target.iri])]

            result += builder.build_ontology(ontology, self._local_name(file.target.file),
                                             self._release_script.prefixes, dependencies, self._working_dir,
                                             self._release_script.iri_prefix)
            self._raise_if_canceled()

            loaded[k] = ontology

        result.warnings = []
        self._set_release_result(result)
        return result.ok()

    @classmethod
    def name(cls) -> str:
        return "BUILD"
