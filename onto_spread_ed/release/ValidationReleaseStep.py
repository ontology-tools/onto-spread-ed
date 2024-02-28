from .ReleaseStep import ReleaseStep
from .common import order_sources
from ..model.ExcelOntology import ExcelOntology
from ..model.Result import Result


class ValidationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "VALIDATION"

    def run(self) -> bool:
        # Validate
        validation_info = dict()
        validation_result = Result(())

        queue = order_sources(self._release_script.files)

        self._total_items = len(queue)

        loaded = dict()
        for k, file in queue:
            self._next_item(item=k)

            result = Result()
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

                self._raise_if_canceled()

            result += ontology.resolve()
            self._raise_if_canceled()

            result += ontology.validate()
            self._raise_if_canceled()

            validation_info[k] = dict(
                valid=result.ok(),
                warnings=result.warnings,
                errors=result.errors
            )

            validation_result += result

            loaded[k] = ontology

        self._set_release_info(validation_info)
        if not validation_result.has_errors() and validation_result.ok():
            self._next_release_step()
        else:
            self._update_release(dict(state="waiting-for-user"))

        return validation_result.ok()
