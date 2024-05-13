import os.path

import pyhornedowl

from .ReleaseStep import ReleaseStep
from .common import order_sources
from ..model.ExcelOntology import ExcelOntology
from ..model.Relation import Relation, OWLPropertyType
from ..model.Result import Result
from ..model.Term import Term


class ValidationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "VALIDATION"

    def load_externals_ontology(self) -> Result[ExcelOntology]:
        result = Result()

        excel_ontology = ExcelOntology(self._release_script.external.target.iri)
        externals_owl = self._local_name(self._release_script.external.target.file)
        if os.path.exists(externals_owl):
            ontology = pyhornedowl.open_ontology(externals_owl)
            for [p, d] in self._config["PREFIXES"]:
                ontology.add_prefix_mapping(p, d)

            for c in ontology.get_classes():
                id = ontology.get_id_for_iri(c)
                labels = ontology.get_annotations(c, self._config['RDFSLABEL'])

                if id is None:
                    result.warning(type='unknown-id', msg=f'Unable to determine id of external term "{c}"')
                if len(labels) == 0:
                    result.warning(type='unknown-label', msg=f'Unable to determine label of external term "{c}"')

                if id is not None:
                    for label in labels:
                        excel_ontology.add_term(Term(
                            id=id,
                            label=label,
                            origin=("<external>", -1),
                            relations=[],
                            sub_class_of=[],
                            equivalent_to=[],
                            disjoint_with=[]
                        ))

            self._raise_if_canceled()

            for r in ontology.get_object_properties():
                id = ontology.get_id_for_iri(r)
                label = ontology.get_annotation(r, self._config['RDFSLABEL'])

                if id is None:
                    result.warning(type='unknown-id', msg=f'Unable to determine id of external relation "{r}"')
                if label is None:
                    result.warning(type='unknown-label', msg=f'Unable to determine label of external relation "{r}"')

                if id is not None and label is not None:
                    excel_ontology.add_relation(Relation(
                        id=id,
                        label=label,
                        origin=("<external>", -1),
                        synonyms=[],
                        relations=[],
                        owl_property_type=OWLPropertyType.ObjectProperty,
                        sub_property_of=[],
                        domain=None,
                        range=None
                    ))
        else:
            result.error(type="external-owl-missing",
                         msg="The external OWL file is missing. Ensure it is build before this step")
            return result

        result.value = excel_ontology
        return result

    def run(self) -> bool:
        # Validate
        validation_info = dict()
        validation_result = Result(())

        queue = order_sources(self._release_script.files)

        self._total_items = len(queue)

        external_ontology_result = self.load_externals_ontology()

        self._raise_if_canceled()

        external = external_ontology_result.value
        validation_result += external_ontology_result

        loaded = dict()
        for k, file in queue:
            self._next_item(item=k)

            result = Result()
            ontology = ExcelOntology(file.target.iri)
            ontology.import_other_excel_ontology(external)

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
