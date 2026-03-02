"""Schema-driven writers for Excel and ROBOT CSV output.

Uses :class:`SchemaDefinition` from the YAML schema as the single source of
truth for column structure and OWL-construct semantics.  Value extraction is
format-agnostic; each writer applies its own serialisation on top.
"""

from __future__ import annotations

import csv
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from .Relation import OWLPropertyType, Relation, UnresolvedRelation
from .SchemaLoader import ColumnDefinition, OwlPropertyMapping, SchemaDefinition
from .Term import UnresolvedTerm, _TermBase
from .TermIdentifier import TermIdentifier

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# OWL constructs written as static Excel columns for terms
_TERM_EXCEL_OWL = {"id", "label", "subClassOf", "disjointWith", "equivalentClass"}

# OWL constructs that map to static ROBOT CSV columns (terms + relations).
# Order is fixed by the ROBOT template convention.
_ROBOT_STATIC_OWL: Dict[str, Tuple[str, str]] = {
    "id":                ("id", "ID"),
    "label":             ("label", "LABEL"),
    "subClassOf":        ("parent class", "SC % SPLIT=;"),
    "subPropertyOf":     ("parent relation", "SP % SPLIT=;"),
    "equivalentClass":   ("logical definition", "EC %"),
    "domain":            ("domain", "DOMAIN"),
    "range":             ("range", "RANGE"),
    "equivalentProperty": ("equivalent relationship", "EP % SPLIT=;"),
}

# ---------------------------------------------------------------------------
# Generic value extraction  (format-agnostic)
# ---------------------------------------------------------------------------


def extract_term_value(col: ColumnDefinition, term: _TermBase) -> Any:
    """Return the raw value for *col* from *term*.  Returns ``None`` when the
    column is not applicable to terms."""

    if col.ignore:
        return None

    owl = col.owl
    if owl == "id":
        return term.id
    if owl == "label":
        return term.label
    if owl == "subClassOf":
        return term.sub_class_of
    if owl == "disjointWith":
        return term.disjoint_with
    if owl == "equivalentClass":
        return term.equivalent_to

    # Named annotation / object_property / data_property
    if isinstance(owl, OwlPropertyMapping):
        return term.get_relation_value(
            TermIdentifier(id=owl.property_id, label=owl.property_label)
        )

    # Internal field (stored as relation with OWLPropertyType.Internal)
    if col.internal is not None:
        return term.get_relation_value(TermIdentifier(label=col.internal))

    return None


def extract_relation_value(col: ColumnDefinition, relation: Relation) -> Any:
    """Return the raw value for *col* from *relation*.  Returns ``None`` when
    the column is not applicable to relations."""

    if col.ignore:
        return None

    owl = col.owl
    if owl == "id":
        return relation.id
    if owl == "label":
        return relation.label
    if owl == "subPropertyOf":
        return relation.sub_property_of
    if owl == "domain":
        return relation.domain
    if owl == "range":
        return relation.range
    if owl == "equivalentProperty":
        return relation.equivalent_relations
    if owl == "inverseOf":
        return relation.inverse_of
    if owl == "entityType":
        return relation.owl_property_type

    # Named annotation on the relation entity itself
    if isinstance(owl, OwlPropertyMapping):
        return next(
            (v for r, v in relation.relations
             if r.id == owl.property_id or r.label == owl.property_label),
            None,
        )

    return None


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_term_identifiers(items: List[TermIdentifier], separator: str = "; ") -> str:
    """``Label [ID]`` serialisation used by Excel output."""
    return separator.join(
        f"{s.label} [{s.id}]" if s.id else (s.label or "")
        for s in items
    )


def _format_id_list(items, separator: str = ";") -> str:
    """Semicolon-joined IDs used by ROBOT CSV output."""
    if not items:
        return ""
    return separator.join(t.id for t in items if t.id is not None)


# ---------------------------------------------------------------------------
# ExcelWriter
# ---------------------------------------------------------------------------

class ExcelWriter:
    """Schema-driven replacement for ``ExcelOntology.to_excel()``."""

    def __init__(self, definition: SchemaDefinition):
        self._definition = definition

    def write(
        self,
        terms: List[UnresolvedTerm],
        used_relations: FrozenSet[UnresolvedRelation],
        include_origin: bool = False,
    ) -> Workbook:
        static_cols = self._static_columns()
        relations = list(used_relations)

        # -- header ---------------------------------------------------------
        header: List[str] = [name for name, _col in static_cols]
        header += [
            (r.label if r.id is None else f"REL '{r.label}'")
            for r in relations
        ]
        if include_origin:
            header.append("origin")

        wb = Workbook()
        ws: Worksheet = wb.active
        ws.append(header)

        # -- rows -----------------------------------------------------------
        for term in terms:
            row: List[Any] = []
            for _name, col in static_cols:
                row.append(self._format_term_cell(col, term))

            for rel in relations:
                row.append(term.get_relation_value(rel.identifier()))

            if include_origin:
                row.append(":".join(str(p) for p in term.origin) if term.origin else "")

            ws.append(row)

        return wb

    # -- helpers ------------------------------------------------------------

    def _static_columns(self) -> List[Tuple[str, ColumnDefinition]]:
        """Return ``(header_name, column_def)`` pairs for static term columns."""
        result: List[Tuple[str, ColumnDefinition]] = []
        for col in self._definition.columns:
            if col.ignore or col.excel_pattern is not None:
                continue
            if isinstance(col.owl, str) and col.owl in _TERM_EXCEL_OWL:
                name = col.excel_names[0] if col.excel_names else col.owl
                result.append((name, col))
        return result

    @staticmethod
    def _format_term_cell(col: ColumnDefinition, term: _TermBase) -> Any:
        """Format a single cell value for Excel output."""
        value = extract_term_value(col, term)
        if value is None:
            return None
        owl = col.owl
        if owl == "subClassOf" or owl == "disjointWith":
            return _format_term_identifiers(value)
        if owl == "equivalentClass":
            return "; ".join(value) if value else ""
        return value


# ---------------------------------------------------------------------------
# RobotCsvWriter
# ---------------------------------------------------------------------------

class RobotCsvWriter:
    """Schema-driven replacement for the CSV generation part of
    ``RobotOntologyBuildService.build_ontology()``.

    ROBOT template instructions are derived from OWL construct types – they
    are **not** stored in the YAML schema.
    """

    def __init__(self, definition: SchemaDefinition):
        self._definition = definition

    # -- public API ---------------------------------------------------------

    def write_csv(self, csv_file, ontology) -> None:
        """Write the ROBOT template CSV into an already-opened *csv_file*.

        *ontology* is an ``ExcelOntology`` instance.
        """
        from .ExcelOntology import ExcelOntology
        assert isinstance(ontology, ExcelOntology)

        internal_relations = [
            r.id for r in ontology.used_relations()
            if r.owl_property_type == OWLPropertyType.Internal
        ]

        # -- build header ---------------------------------------------------
        header = self._build_header(ontology)

        fieldnames = [k for k, _ in header]
        writer = csv.DictWriter(
            csv_file, fieldnames, delimiter=",", quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerow(dict(header))

        # -- term rows ------------------------------------------------------
        for term in ontology.terms():
            row = self._term_row(term, internal_relations)
            writer.writerow(row)

        # -- relation rows --------------------------------------------------
        for relation in ontology.relations():
            if relation.owl_property_type == OWLPropertyType.Internal:
                continue
            row = self._relation_row(relation)
            writer.writerow(row)

    # -- header building ----------------------------------------------------

    def _build_header(self, ontology) -> List[Tuple[str, str]]:
        """Return ``[(column_name, robot_instruction), ...]``."""
        header: List[Tuple[str, str]] = [("type", "TYPE")]

        # Static columns from schema in fixed ROBOT order
        for owl_str, (col_name, instruction) in _ROBOT_STATIC_OWL.items():
            # Only include if the schema actually has this construct
            if self._schema_has_construct(owl_str):
                header.append((col_name, instruction))

        # Dynamic relation columns from used_relations()
        for relation in ontology.used_relations():
            if relation.owl_property_type == OWLPropertyType.AnnotationProperty:
                header.append(
                    (f"REL '{relation.label}'", f"A {relation.id} SPLIT=;")
                )
            elif relation.owl_property_type in (
                OWLPropertyType.DataProperty, OWLPropertyType.ObjectProperty,
            ):
                header.append(
                    (f"REL '{relation.label}'",
                     f"SC '{relation.label}' some % SPLIT=;")
                )
            # Internal and other types are skipped

        return header

    def _schema_has_construct(self, owl_str: str) -> bool:
        """Check whether the schema defines a column with the given simple OWL construct."""
        return any(
            col.owl == owl_str
            for col in self._definition.columns
            if isinstance(col.owl, str)
        )

    # -- row building -------------------------------------------------------

    @staticmethod
    def _term_row(term, internal_relations: List[Optional[str]]) -> Dict[str, Any]:
        """Build a ROBOT CSV row dict for a class term."""
        row: Dict[str, Any] = {
            "type": "class",
            "id": term.id,
            "label": term.label,
            "parent class": ";".join(t.id for t in term.sub_class_of),
            "logical definition": ";".join(t for t in term.equivalent_to),
        }

        for relation, value in term.relations:
            if relation.id in internal_relations:
                continue
            row[f"REL '{relation.label}'"] = (
                value.id if isinstance(value, TermIdentifier) else value
            )

        return row

    @staticmethod
    def _relation_row(relation: Relation) -> Dict[str, Any]:
        """Build a ROBOT CSV row dict for a property relation."""
        typ = {
            OWLPropertyType.AnnotationProperty: "annotation property",
            OWLPropertyType.ObjectProperty: "object property",
            OWLPropertyType.DataProperty: "data property",
        }[relation.owl_property_type]

        row: Dict[str, Any] = {
            "type": typ,
            "id": relation.id,
            "label": relation.label,
            "parent relation": ";".join(r.id for r in relation.sub_property_of),
            "domain": relation.domain.id if relation.domain is not None else None,
            "range": relation.range.id if relation.range is not None else None,
            "equivalent relationship": ";".join(
                p.id for p in relation.equivalent_relations
            ),
        }

        for r, value in relation.relations:
            row[f"REL '{r.label}'"] = value

        return row
