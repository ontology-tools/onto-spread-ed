"""Schema-driven OWL reader for importing ontologies.

Uses :class:`SchemaDefinition` from the YAML schema to determine which OWL
constructs to extract from an ontology loaded via pyhornedowl.  The reader
produces :class:`Term` and :class:`Relation` objects that populate an
:class:`ExcelOntology`.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import pyhornedowl as ho
from pyhornedowl.model import (
    Class as OwlClass,
    DataProperty as OwlDataProperty,
    DataPropertyDomain,
    DataPropertyRange,
    Datatype,
    DisjointClasses,
    EquivalentClasses,
    EquivalentDataProperties,
    EquivalentObjectProperties,
    IRI,
    InverseObjectProperties,
    ObjectProperty as OwlObjectProperty,
    ObjectPropertyDomain,
    ObjectPropertyRange,
    ObjectSomeValuesFrom,
    SimpleLiteral,
    LanguageLiteral,
    DatatypeLiteral,
    SubAnnotationPropertyOf,
    SubClassOf,
    SubDataPropertyOf,
    SubObjectPropertyOf,
)

from .. import constants
from ..model.Relation import OWLPropertyType, Relation
from ..model.Result import Result
from ..model.SchemaLoader import OwlPropertyMapping, SchemaDefinition
from ..model.Term import Term
from ..model.TermIdentifier import TermIdentifier

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _annotation_value_str(av) -> Optional[str]:
    """Extract a string from a pyhornedowl annotation value."""
    if isinstance(av, SimpleLiteral):
        return av.literal
    if isinstance(av, LanguageLiteral):
        return av.literal
    if isinstance(av, DatatypeLiteral):
        return av.literal
    if isinstance(av, IRI):
        return str(av)
    return str(av) if av is not None else None


def _iri_str(entity) -> str:
    """Get string IRI from a pyhornedowl entity with a ``.first`` attribute."""
    return str(entity.first)


# ---------------------------------------------------------------------------
# OwlReader
# ---------------------------------------------------------------------------


class OwlReader:
    """Schema-driven replacement for ``ExcelOntology.from_owl()``.

    Iterates :attr:`SchemaDefinition.columns` to decide which OWL data to
    extract from a pyhornedowl ontology.  Columns marked ``ignore`` or
    ``internal`` are skipped (they have no OWL representation).
    """

    def __init__(self, definition: SchemaDefinition):
        self._definition = definition

        # Pre-scan schema to know which constructs to extract
        self._named_annotations: List[OwlPropertyMapping] = []
        self._has_object_property_pattern = False
        self._has_annotation_pattern = False
        self._class_constructs: Set[str] = set()
        self._property_constructs: Set[str] = set()

        for col in definition.columns:
            if col.ignore or col.internal is not None:
                continue
            owl = col.owl
            if isinstance(owl, str):
                if owl in ("id", "label", "subClassOf", "disjointWith", "equivalentClass"):
                    self._class_constructs.add(owl)
                if owl in ("id", "label", "subPropertyOf", "domain", "range",
                           "inverseOf", "equivalentProperty", "entityType"):
                    self._property_constructs.add(owl)
            elif isinstance(owl, OwlPropertyMapping):
                if owl.property_id is not None:
                    self._named_annotations.append(owl)
                elif col.excel_pattern is not None:
                    if owl.construct == "object_property":
                        self._has_object_property_pattern = True
                    elif owl.construct == "annotation":
                        self._has_annotation_pattern = True

    # -- public API ---------------------------------------------------------

    def read(
        self,
        owl_source: str,
        prefixes: Dict[str, str],
        origin: str = "<external>",
    ) -> "Result":
        from .ExcelOntology import ExcelOntology, get_id  # noqa: F811

        result: Result = Result()
        ontology = ho.open_ontology(owl_source)
        ontology.prefix_mapping.add_default_prefix_names()

        excel_ontology = ExcelOntology(str(ontology.get_iri()))
        for p, d in prefixes.items():
            ontology.prefix_mapping.add_prefix(p, d)

        # Resolve named annotation property IRIs once
        named_ann_iris = self._resolve_named_annotation_iris(ontology)

        # --- Classes -> Term objects ---
        for class_iri in ontology.get_classes():
            terms = self._read_class(ontology, class_iri, origin, result, get_id, named_ann_iris)
            for term in terms:
                excel_ontology.add_term(term)

        # --- Object properties -> Relation objects ---
        for op_iri in ontology.get_object_properties():
            relation = self._read_property(
                ontology, op_iri, OWLPropertyType.ObjectProperty, origin, result, get_id, named_ann_iris
            )
            if relation is not None:
                excel_ontology.add_relation(relation)

        # --- Data properties -> Relation objects ---
        for dp_iri in ontology.get_data_properties():
            relation = self._read_property(
                ontology, dp_iri, OWLPropertyType.DataProperty, origin, result, get_id, named_ann_iris
            )
            if relation is not None:
                excel_ontology.add_relation(relation)

        # --- Annotation properties -> Relation objects ---
        for ap_iri in ontology.get_annotation_properties():
            relation = self._read_property(
                ontology, ap_iri, OWLPropertyType.AnnotationProperty, origin, result, get_id, named_ann_iris
            )
            if relation is not None:
                excel_ontology.add_relation(relation)

        result.value = excel_ontology
        return result

    # -- schema pre-computation --------------------------------------------

    def _resolve_named_annotation_iris(self, ontology: ho.PyIndexedOntology) -> Dict[str, str]:
        """Map ``property_id`` CURIEs to full IRIs for named annotation columns.

        Returns ``{property_id: full_iri}`` for each named annotation where
        the IRI could be resolved.
        """
        result: Dict[str, str] = {}
        for ann in self._named_annotations:
            iri = ontology.get_iri_for_id(ann.property_id)
            if iri is not None:
                result[ann.property_id] = iri
        return result

    # -- class reading ------------------------------------------------------

    def _read_class(
        self,
        ontology: ho.PyIndexedOntology,
        class_iri: str,
        origin: str,
        result: Result,
        get_id,
        named_ann_iris: Dict[str, str],
    ) -> List[Term]:
        entity_id = get_id(ontology, class_iri)

        if entity_id is None:
            result.warning(type='unknown-id',
                           msg=f'Unable to determine id of external term "{class_iri}"')
            return []

        labels = ontology.get_annotations(class_iri, constants.RDFS_LABEL)
        if len(labels) == 0:
            result.warning(type='unknown-label',
                           msg=f'Unable to determine label of external term "{class_iri}"')

        # Fetch axioms once for this class
        axioms = ontology.get_axioms_for_iri(class_iri)

        # Extract data based on schema constructs
        superclasses: List[TermIdentifier] = []
        if "subClassOf" in self._class_constructs:
            superclasses = self._extract_superclasses(ontology, class_iri, get_id)

        disjoint_with: List[TermIdentifier] = []
        if "disjointWith" in self._class_constructs:
            disjoint_with = self._extract_disjoint_classes(ontology, class_iri, axioms, get_id)

        equivalent_to: List[str] = []
        if "equivalentClass" in self._class_constructs:
            equivalent_to = self._extract_equivalent_classes(ontology, class_iri, axioms, get_id)

        # Extract relations: named annotations + object property restrictions
        relations: List[Tuple[TermIdentifier, Any]] = []

        # Named annotation columns
        for ann in self._named_annotations:
            full_iri = named_ann_iris.get(ann.property_id)
            if full_iri is None:
                continue
            values = ontology.get_annotations(class_iri, full_iri)
            for v in values:
                relations.append((
                    TermIdentifier(id=ann.property_id, label=ann.property_label),
                    v,
                ))

        # Object property restrictions (from pattern columns)
        if self._has_object_property_pattern:
            obj_relations = self._extract_object_property_relations(ontology, class_iri, axioms, get_id)
            relations.extend(obj_relations)

        # Create one Term per label (preserving existing behavior)
        terms = []
        for label in labels:
            terms.append(Term(
                id=entity_id,
                label=label,
                origin=(origin, -1),
                relations=relations,
                sub_class_of=superclasses,
                equivalent_to=equivalent_to,
                disjoint_with=disjoint_with,
            ))
        return terms

    # -- property reading ---------------------------------------------------

    def _read_property(
        self,
        ontology: ho.PyIndexedOntology,
        prop_iri: str,
        prop_type: OWLPropertyType,
        origin: str,
        result: Result,
        get_id,
        named_ann_iris: Dict[str, str],
    ) -> Optional[Relation]:
        entity_id = get_id(ontology, prop_iri)
        label = ontology.get_annotation(prop_iri, constants.RDFS_LABEL)

        if entity_id is None:
            result.warning(type='unknown-id',
                           msg=f'Unable to determine id of {origin} relation "{prop_iri}"')
            return None
        if label is None:
            result.warning(type='unknown-label',
                           msg=f'Unable to determine label of {origin} relation "{prop_iri}"')
            return None

        axioms = ontology.get_axioms_for_iri(prop_iri)

        sub_property_of: List[TermIdentifier] = []
        if "subPropertyOf" in self._property_constructs:
            sub_property_of = self._extract_sub_property_of(ontology, prop_iri, prop_type, axioms, get_id)

        domain: Optional[TermIdentifier] = None
        if "domain" in self._property_constructs:
            domain = self._extract_domain(ontology, prop_iri, prop_type, axioms, get_id)

        range_val: Optional[TermIdentifier] = None
        if "range" in self._property_constructs:
            range_val = self._extract_range(ontology, prop_iri, prop_type, axioms, get_id)

        inverse_of: List[TermIdentifier] = []
        if "inverseOf" in self._property_constructs and prop_type == OWLPropertyType.ObjectProperty:
            inverse_of = self._extract_inverse_of(ontology, prop_iri, axioms, get_id)

        equivalent_relations: List[TermIdentifier] = []
        if "equivalentProperty" in self._property_constructs:
            equivalent_relations = self._extract_equivalent_properties(
                ontology, prop_iri, prop_type, axioms, get_id
            )

        # Named annotation relations on the property entity
        relations: List[Tuple[TermIdentifier, Any]] = []
        for ann in self._named_annotations:
            full_iri = named_ann_iris.get(ann.property_id)
            if full_iri is None:
                continue
            values = ontology.get_annotations(prop_iri, full_iri)
            for v in values:
                relations.append((
                    TermIdentifier(id=ann.property_id, label=ann.property_label),
                    v,
                ))

        return Relation(
            id=entity_id,
            label=label,
            origin=(origin, -1),
            equivalent_relations=equivalent_relations,
            inverse_of=inverse_of,
            relations=relations,
            owl_property_type=prop_type,
            sub_property_of=sub_property_of,
            domain=domain,
            range=range_val,
        )

    # -- axiom extraction helpers -------------------------------------------

    @staticmethod
    def _extract_superclasses(
        ontology: ho.PyIndexedOntology,
        class_iri: str,
        get_id,
    ) -> List[TermIdentifier]:
        superclasses = ontology.get_superclasses(class_iri)
        result = []
        for s in superclasses:
            s_id = get_id(ontology, s)
            s_label = ontology.get_annotation(s, constants.RDFS_LABEL)
            if s_id is not None:
                result.append(TermIdentifier(s_id, s_label))
        return result

    @staticmethod
    def _extract_disjoint_classes(
        ontology: ho.PyIndexedOntology,
        class_iri: str,
        axioms,
        get_id,
    ) -> List[TermIdentifier]:
        result: List[TermIdentifier] = []
        for a in axioms:
            comp = a.component
            if isinstance(comp, DisjointClasses):
                for ce in comp.first:
                    if isinstance(ce, OwlClass):
                        other_iri = _iri_str(ce)
                        if other_iri != class_iri:
                            other_id = get_id(ontology, other_iri)
                            other_label = ontology.get_annotation(other_iri, constants.RDFS_LABEL)
                            if other_id is not None:
                                result.append(TermIdentifier(id=other_id, label=other_label))
        return result

    @staticmethod
    def _extract_equivalent_classes(
        ontology: ho.PyIndexedOntology,
        class_iri: str,
        axioms,
        get_id,
    ) -> List[str]:
        result: List[str] = []
        for a in axioms:
            comp = a.component
            if isinstance(comp, EquivalentClasses):
                for ce in comp.first:
                    if isinstance(ce, OwlClass):
                        other_iri = _iri_str(ce)
                        if other_iri != class_iri:
                            other_id = get_id(ontology, other_iri)
                            if other_id is not None:
                                result.append(other_id)
        return result

    @staticmethod
    def _extract_object_property_relations(
        ontology: ho.PyIndexedOntology,
        class_iri: str,
        axioms,
        get_id,
    ) -> List[Tuple[TermIdentifier, Any]]:
        """Extract ``SubClassOf(ObjectSomeValuesFrom(...))`` restrictions."""
        relations: List[Tuple[TermIdentifier, Any]] = []
        for a in axioms:
            comp = a.component
            if (isinstance(comp, SubClassOf)
                    and isinstance(comp.sup, ObjectSomeValuesFrom)
                    and isinstance(comp.sup.ope, OwlObjectProperty)
                    and isinstance(comp.sup.bce, OwlClass)):
                rel_iri = _iri_str(comp.sup.ope)
                target_iri = _iri_str(comp.sup.bce)
                rel_id = get_id(ontology, rel_iri)
                rel_label = ontology.get_annotation(rel_iri, constants.RDFS_LABEL)
                target_id = get_id(ontology, target_iri)
                target_label = ontology.get_annotation(target_iri, constants.RDFS_LABEL)
                if rel_id is not None or rel_label is not None:
                    relations.append((
                        TermIdentifier(id=rel_id, label=rel_label),
                        TermIdentifier(id=target_id, label=target_label),
                    ))
        return relations

    @staticmethod
    def _extract_sub_property_of(
        ontology: ho.PyIndexedOntology,
        prop_iri: str,
        prop_type: OWLPropertyType,
        axioms,
        get_id,
    ) -> List[TermIdentifier]:
        result: List[TermIdentifier] = []
        for a in axioms:
            comp = a.component
            if prop_type == OWLPropertyType.ObjectProperty and isinstance(comp, SubObjectPropertyOf):
                if isinstance(comp.sub, OwlObjectProperty) and _iri_str(comp.sub) == prop_iri:
                    if isinstance(comp.sup, OwlObjectProperty):
                        sup_iri = _iri_str(comp.sup)
                        sup_id = get_id(ontology, sup_iri)
                        sup_label = ontology.get_annotation(sup_iri, constants.RDFS_LABEL)
                        if sup_id is not None:
                            result.append(TermIdentifier(id=sup_id, label=sup_label))
            elif prop_type == OWLPropertyType.DataProperty and isinstance(comp, SubDataPropertyOf):
                if _iri_str(comp.sub) == prop_iri:
                    sup_iri = _iri_str(comp.sup)
                    sup_id = get_id(ontology, sup_iri)
                    sup_label = ontology.get_annotation(sup_iri, constants.RDFS_LABEL)
                    if sup_id is not None:
                        result.append(TermIdentifier(id=sup_id, label=sup_label))
            elif prop_type == OWLPropertyType.AnnotationProperty and isinstance(comp, SubAnnotationPropertyOf):
                if _iri_str(comp.sub) == prop_iri:
                    sup_iri = _iri_str(comp.sup)
                    sup_id = get_id(ontology, sup_iri)
                    sup_label = ontology.get_annotation(sup_iri, constants.RDFS_LABEL)
                    if sup_id is not None:
                        result.append(TermIdentifier(id=sup_id, label=sup_label))
        return result

    @staticmethod
    def _extract_domain(
        ontology: ho.PyIndexedOntology,
        prop_iri: str,
        prop_type: OWLPropertyType,
        axioms,
        get_id,
    ) -> Optional[TermIdentifier]:
        for a in axioms:
            comp = a.component
            if prop_type == OWLPropertyType.ObjectProperty and isinstance(comp, ObjectPropertyDomain):
                if isinstance(comp.ope, OwlObjectProperty) and _iri_str(comp.ope) == prop_iri:
                    if isinstance(comp.ce, OwlClass):
                        domain_iri = _iri_str(comp.ce)
                        domain_id = get_id(ontology, domain_iri)
                        domain_label = ontology.get_annotation(domain_iri, constants.RDFS_LABEL)
                        return TermIdentifier(id=domain_id, label=domain_label)
            elif prop_type == OWLPropertyType.DataProperty and isinstance(comp, DataPropertyDomain):
                if _iri_str(comp.dp) == prop_iri:
                    if isinstance(comp.ce, OwlClass):
                        domain_iri = _iri_str(comp.ce)
                        domain_id = get_id(ontology, domain_iri)
                        domain_label = ontology.get_annotation(domain_iri, constants.RDFS_LABEL)
                        return TermIdentifier(id=domain_id, label=domain_label)
        return None

    @staticmethod
    def _extract_range(
        ontology: ho.PyIndexedOntology,
        prop_iri: str,
        prop_type: OWLPropertyType,
        axioms,
        get_id,
    ) -> Optional[TermIdentifier]:
        for a in axioms:
            comp = a.component
            if prop_type == OWLPropertyType.ObjectProperty and isinstance(comp, ObjectPropertyRange):
                if isinstance(comp.ope, OwlObjectProperty) and _iri_str(comp.ope) == prop_iri:
                    if isinstance(comp.ce, OwlClass):
                        range_iri = _iri_str(comp.ce)
                        range_id = get_id(ontology, range_iri)
                        range_label = ontology.get_annotation(range_iri, constants.RDFS_LABEL)
                        return TermIdentifier(id=range_id, label=range_label)
            elif prop_type == OWLPropertyType.DataProperty and isinstance(comp, DataPropertyRange):
                if _iri_str(comp.dp) == prop_iri:
                    if isinstance(comp.dr, Datatype):
                        range_iri = _iri_str(comp.dr)
                        range_id = get_id(ontology, range_iri)
                        return TermIdentifier(id=range_id, label=None)
        return None

    @staticmethod
    def _extract_inverse_of(
        ontology: ho.PyIndexedOntology,
        prop_iri: str,
        axioms,
        get_id,
    ) -> List[TermIdentifier]:
        result: List[TermIdentifier] = []
        for a in axioms:
            comp = a.component
            if isinstance(comp, InverseObjectProperties):
                first_iri = _iri_str(comp.first)
                second_iri = _iri_str(comp.second)
                if first_iri == prop_iri:
                    other_iri = second_iri
                elif second_iri == prop_iri:
                    other_iri = first_iri
                else:
                    continue
                other_id = get_id(ontology, other_iri)
                other_label = ontology.get_annotation(other_iri, constants.RDFS_LABEL)
                if other_id is not None:
                    result.append(TermIdentifier(id=other_id, label=other_label))
        return result

    @staticmethod
    def _extract_equivalent_properties(
        ontology: ho.PyIndexedOntology,
        prop_iri: str,
        prop_type: OWLPropertyType,
        axioms,
        get_id,
    ) -> List[TermIdentifier]:
        result: List[TermIdentifier] = []
        for a in axioms:
            comp = a.component
            if prop_type == OWLPropertyType.ObjectProperty and isinstance(comp, EquivalentObjectProperties):
                for ope in comp.first:
                    if isinstance(ope, OwlObjectProperty):
                        other_iri = _iri_str(ope)
                        if other_iri != prop_iri:
                            other_id = get_id(ontology, other_iri)
                            other_label = ontology.get_annotation(other_iri, constants.RDFS_LABEL)
                            if other_id is not None:
                                result.append(TermIdentifier(id=other_id, label=other_label))
            elif prop_type == OWLPropertyType.DataProperty and isinstance(comp, EquivalentDataProperties):
                for dp in comp.first:
                    if isinstance(dp, OwlDataProperty):
                        other_iri = _iri_str(dp)
                        if other_iri != prop_iri:
                            other_id = get_id(ontology, other_iri)
                            other_label = ontology.get_annotation(other_iri, constants.RDFS_LABEL)
                            if other_id is not None:
                                result.append(TermIdentifier(id=other_id, label=other_label))
        return result
