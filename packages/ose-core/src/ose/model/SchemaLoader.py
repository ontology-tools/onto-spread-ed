from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Literal, Optional, Union

import dacite
import yaml

from .ColumnMapping import (
    ChoiceColumnMapping,
    ColumnMappingFactory,
    ColumnMappingKind,
    IRIMapping,
    LabelMapping,
    ManchesterSyntaxMapping,
    ParentMapping,
    PrefixColumnMapping,
    RelationColumnMapping,
    SimpleColumnMapping,
    SingletonMappingFactory,
    PatternMappingFactory,
    TermMapping,
)
from .Relation import OWLPropertyType, Relation
from .TermIdentifier import TermIdentifier

if TYPE_CHECKING:
    from .Schema import Schema


OwlConstructType = Literal["annotation", "object_property", "data_property"]
"""Allowed values for :attr:`OwlPropertyMapping.construct`."""

ValueFormat = Literal["text", "manchester_syntax", "term_reference", "iri", "prefix", "choice"]
"""Allowed values for :attr:`ColumnDefinition.value_format`."""


def _to_camel_case(name: str) -> str:
    """Convert ``UPPER_SNAKE_CASE`` to ``camelCase``."""
    parts = name.lower().split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


# Members where the YAML name doesn't follow camelCase of the enum name.
# Maps ColumnMappingKind → list of YAML alias strings.
_OWL_NAME_OVERRIDES: dict[ColumnMappingKind, list[str]] = {
    ColumnMappingKind.EQUIVALENT_TO: ["equivalentClass", "equivalentProperty"],
    ColumnMappingKind.RELATION_TYPE: ["entityType"],
    ColumnMappingKind.PLAIN: ["intermediates"],
}

# Members that are not valid as simple ``owl`` strings in the YAML schema.
_EXCLUDED_FROM_OWL = {ColumnMappingKind.IGNORE, ColumnMappingKind.RELATION, ColumnMappingKind.SYNONYMS}

_OWL_TO_KIND: dict[str, ColumnMappingKind] = {}
for _kind in ColumnMappingKind:
    if _kind in _EXCLUDED_FROM_OWL:
        continue
    if _kind in _OWL_NAME_OVERRIDES:
        for _yaml_name in _OWL_NAME_OVERRIDES[_kind]:
            _OWL_TO_KIND[_yaml_name] = _kind
    else:
        _OWL_TO_KIND[_to_camel_case(_kind.name)] = _kind

VALID_OWL_CONSTRUCTS: frozenset[str] = frozenset(_OWL_TO_KIND.keys())
"""Set of valid string values for :attr:`ColumnDefinition.owl`."""


@dataclass
class OwlPropertyMapping:
    """Compound OWL mapping used when ``owl`` is a dict in the YAML schema.

    Represents annotation assertions, object property restrictions, or data
    property assertions where the OWL property itself must be identified.
    """

    construct: OwlConstructType
    """The kind of OWL construct: ``"annotation"``, ``"object_property"``, or ``"data_property"``."""

    property_id: Optional[str] = None
    """CURIE of the OWL property, e.g. ``"IAO:0000115"``. ``None`` for pattern-based columns
    where the property is extracted from the column name at runtime."""

    property_label: Optional[str] = None
    """Human-readable label of the OWL property, e.g. ``"definition"``. ``None`` for
    pattern-based columns where the label is extracted from the column name at runtime."""


@dataclass
class ColumnDefinition:
    """A single column mapping entry from the YAML schema.

    Exactly one of ``ignore``, ``internal``, or ``owl`` must be set to determine
    how the column is handled. Column identification uses either ``excel_names``
    (exact match) or ``excel_pattern`` (regex), but not both.
    """

    excel_names: Optional[List[str]] = None
    """Exact Excel column header names that this definition matches.
    Mutually exclusive with ``excel_pattern``."""

    excel_pattern: Optional[str] = None
    """Regex pattern for matching dynamic column names (e.g. ``"REL '([^']+)'"``).
    Capture group 1 is used as the relation label. Mutually exclusive with ``excel_names``."""

    ignore: Optional[bool] = None
    """If ``True``, columns matching ``excel_names`` are explicitly ignored."""

    owl: Optional[Union[str, OwlPropertyMapping]] = None
    """The OWL construct this column maps to. Either a string from
    :data:`VALID_OWL_CONSTRUCTS` (e.g. ``"id"``, ``"label"``, ``"subClassOf"``)
    or an :class:`OwlPropertyMapping` for annotation/object_property/data_property columns."""

    internal: Optional[str] = None
    """Internal field name when the column has no OWL representation
    (e.g. ``"informalDefinition"``). The value is stored as a relation
    with ``OWLPropertyType.Internal``."""

    value_format: Optional[ValueFormat] = None
    """Override the default value format for the OWL construct."""

    separator: Optional[str] = None
    """Delimiter for multi-valued cells (e.g. ``";"``). ``None`` means single-valued."""

    choices: Optional[List[str]] = None
    """Valid values for choice-type columns (e.g. entity type)."""

    require_id: Optional[bool] = None
    """If ``True``, parsed term references must include an ID component."""

    require_label: Optional[bool] = None
    """If ``True``, parsed term references must include a label component."""

    def __post_init__(self) -> None:
        has_names = self.excel_names is not None
        has_pattern = self.excel_pattern is not None
        if has_names and has_pattern:
            raise ValueError("excel_names and excel_pattern are mutually exclusive")
        if not has_names and not has_pattern:
            raise ValueError("Either excel_names or excel_pattern must be set")

        modes = (self.ignore is True) + (self.internal is not None) + (self.owl is not None)
        if modes != 1:
            raise ValueError(
                f"Exactly one of ignore, internal, or owl must be set (got {modes})"
            )

        if has_pattern and not isinstance(self.owl, OwlPropertyMapping):
            raise ValueError("excel_pattern requires owl to be an OwlPropertyMapping (dict)")

        if isinstance(self.owl, str) and self.owl not in VALID_OWL_CONSTRUCTS:
            raise ValueError(
                f"Unknown owl construct {self.owl!r}, valid values: {sorted(VALID_OWL_CONSTRUCTS)}"
            )


@dataclass
class SchemaDefinition:
    """Top-level structure of a YAML schema file.

    Loaded from YAML via ``dacite.from_dict`` and converted to a :class:`Schema`
    by :class:`SchemaLoader`.
    """

    version: str
    """Schema format version (currently ``"1"``)."""

    columns: List[ColumnDefinition]
    """Ordered list of column mapping definitions."""

    ignored_columns: List[str] = field(default_factory=list)
    """Column names that are silently ignored (not mapped and not flagged as unknown)."""


# Mapping from simple owl construct strings to ColumnMappingKind
_OWL_TO_KIND = {
    "id": ColumnMappingKind.ID,
    "label": ColumnMappingKind.LABEL,
    "subClassOf": ColumnMappingKind.SUB_CLASS_OF,
    "subPropertyOf": ColumnMappingKind.SUB_PROPERTY_OF,
    "equivalentClass": ColumnMappingKind.EQUIVALENT_TO,
    "equivalentProperty": ColumnMappingKind.EQUIVALENT_TO,
    "disjointWith": ColumnMappingKind.DISJOINT_WITH,
    "domain": ColumnMappingKind.DOMAIN,
    "range": ColumnMappingKind.RANGE,
    "inverseOf": ColumnMappingKind.INVERSE_OF,
    "entityType": ColumnMappingKind.RELATION_TYPE,
    # Import schema constructs
    "ontologyId": ColumnMappingKind.ONTOLOGY_ID,
    "ontologyIri": ColumnMappingKind.ONTOLOGY_IRI,
    "excludedImportId": ColumnMappingKind.EXCLUDED_IMPORT_ID,
    "rootId": ColumnMappingKind.ROOT_ID,
    "versionIri": ColumnMappingKind.VERSION_IRI,
    "importedId": ColumnMappingKind.IMPORTED_ID,
    "intermediates": ColumnMappingKind.PLAIN,
    "prefix": ColumnMappingKind.PREFIX,
}


class SchemaLoader:
    @staticmethod
    def load(yaml_path: str) -> Schema:
        definition = SchemaLoader.load_definition(yaml_path)
        return SchemaLoader.from_definition(definition)

    @staticmethod
    def load_definition(yaml_path: str) -> SchemaDefinition:
        """Load a YAML schema file and return the raw :class:`SchemaDefinition`."""
        with open(yaml_path, "r") as f:
            raw = yaml.safe_load(f)

        return dacite.from_dict(
            data_class=SchemaDefinition,
            data=raw,
            config=dacite.Config(strict=True),
        )

    @staticmethod
    def from_definition(definition: SchemaDefinition) -> "Schema":
        from .Schema import Schema

        factories: List[ColumnMappingFactory] = []
        for col in definition.columns:
            factories.append(SchemaLoader._build_factory(col))

        return Schema(factories, definition.ignored_columns)

    @staticmethod
    def _build_factory(col: ColumnDefinition) -> ColumnMappingFactory:
        # Explicitly ignored columns
        if col.ignore:
            names = col.excel_names or []
            mappings = []
            for name in names:
                mappings.append(
                    SingletonMappingFactory(
                        [name], SimpleColumnMapping(ColumnMappingKind.IGNORE, name)
                    )
                )
            # For multiple ignored names, wrap them so each matches independently
            if len(mappings) == 1:
                return mappings[0]
            return _MultiFactory(mappings)

        # Internal fields (no OWL mapping)
        if col.internal is not None:
            names = col.excel_names or []
            identifier = TermIdentifier(id=None, label=col.internal)
            return SingletonMappingFactory(
                names,
                RelationColumnMapping(
                    Relation(
                        identifier.id, identifier.label, [], [],
                        OWLPropertyType.Internal, [], None, None, [], ("<schema>", 0),
                    ),
                    names[0] if names else col.internal,
                    col.separator,
                ),
            )

        # Pattern-based columns (REL '...', ANN '...')
        if col.excel_pattern is not None:
            return SchemaLoader._build_pattern_factory(col)

        # Compound OWL mapping (annotation, object_property, data_property)
        if isinstance(col.owl, OwlPropertyMapping):
            return SchemaLoader._build_relation_factory(col)

        # Simple OWL construct string
        if isinstance(col.owl, str):
            return SchemaLoader._build_simple_factory(col)

        raise ValueError(f"Invalid column definition: {col}")

    @staticmethod
    def _build_simple_factory(col: ColumnDefinition) -> ColumnMappingFactory:
        names = col.excel_names or []
        owl = col.owl
        kind = _OWL_TO_KIND.get(owl)
        if kind is None:
            raise ValueError(f"Unknown owl construct: {owl}")

        name = names[0] if names else owl

        # ID and plain text fields
        if owl in ("id", "intermediates"):
            return SingletonMappingFactory(names, SimpleColumnMapping(kind, name))

        # Label
        if owl == "label":
            return SingletonMappingFactory(names, LabelMapping(name))

        # Parent hierarchy
        if owl in ("subClassOf", "subPropertyOf"):
            return SingletonMappingFactory(names, ParentMapping(kind=kind, name=name))

        # Equivalent class — depends on value_format
        if owl == "equivalentClass":
            if col.value_format == "manchester_syntax":
                return SingletonMappingFactory(
                    names, ManchesterSyntaxMapping(kind=kind, name=name)
                )
            return SingletonMappingFactory(
                names,
                TermMapping(
                    kind=kind, name=name, separator=col.separator,
                    require_id=col.require_id or False,
                    require_label=col.require_label or False,
                ),
            )

        # Equivalent property, disjoint, domain, range, inverse
        if owl in ("equivalentProperty", "disjointWith", "domain", "range", "inverseOf"):
            return SingletonMappingFactory(
                names,
                TermMapping(
                    kind=kind, name=name, separator=col.separator,
                    require_id=col.require_id or False,
                    require_label=col.require_label or False,
                ),
            )

        # Entity type
        if owl == "entityType":
            choices = col.choices or [t.name for t in OWLPropertyType]
            return SingletonMappingFactory(
                names, ChoiceColumnMapping(kind=kind, name=name, choices=choices)
            )

        # Import schema: IRI fields
        if owl in ("ontologyIri", "versionIri"):
            return SingletonMappingFactory(names, IRIMapping(kind=kind, name=name))

        # Import schema: ontologyId
        if owl == "ontologyId":
            return SingletonMappingFactory(names, SimpleColumnMapping(kind, name))

        # Import schema: term reference fields
        if owl in ("excludedImportId", "rootId", "importedId"):
            return SingletonMappingFactory(
                names,
                TermMapping(
                    kind=kind, name=name, separator=col.separator,
                    require_id=col.require_id or False,
                    require_label=col.require_label or False,
                ),
            )

        # Import schema: prefix
        if owl == "prefix":
            return SingletonMappingFactory(
                names, PrefixColumnMapping(name=name, separator=col.separator)
            )

        raise ValueError(f"Unhandled owl construct: {owl}")

    @staticmethod
    def _build_relation_factory(col: ColumnDefinition) -> ColumnMappingFactory:
        names = col.excel_names or []
        prop = col.owl
        assert isinstance(prop, OwlPropertyMapping)

        construct_to_type = {
            "annotation": OWLPropertyType.AnnotationProperty,
            "object_property": OWLPropertyType.ObjectProperty,
            "data_property": OWLPropertyType.DataProperty,
        }
        property_type = construct_to_type.get(prop.construct)
        if property_type is None:
            raise ValueError(f"Unknown construct type: {prop.construct}")

        identifier = TermIdentifier(id=prop.property_id, label=prop.property_label)
        name = names[0] if names else (prop.property_label or prop.property_id or "unknown")

        return SingletonMappingFactory(
            names,
            RelationColumnMapping(
                Relation(
                    identifier.id, identifier.label, [], [],
                    property_type, [], None, None, [], ("<schema>", 0),
                ),
                name,
                col.separator,
            ),
        )

    @staticmethod
    def _build_pattern_factory(col: ColumnDefinition) -> ColumnMappingFactory:
        prop = col.owl
        assert isinstance(prop, OwlPropertyMapping)

        construct_to_type = {
            "annotation": OWLPropertyType.AnnotationProperty,
            "object_property": OWLPropertyType.ObjectProperty,
            "data_property": OWLPropertyType.DataProperty,
        }
        relation_kind = construct_to_type.get(prop.construct, OWLPropertyType.AnnotationProperty)
        separator = col.separator

        pattern = col.excel_pattern

        def factory(origin: str, rel_name: str, match: re.Match) -> RelationColumnMapping:
            identifier = TermIdentifier(label=match.group(1))
            return RelationColumnMapping(
                Relation(
                    identifier.id, identifier.label, [], [],
                    relation_kind, [], None, None, [], (origin, 0),
                ),
                f"REL {rel_name}",
                separator,
            )

        return PatternMappingFactory(pattern, factory)


class _MultiFactory(ColumnMappingFactory):
    """Wraps multiple factories so that a single ColumnDefinition with multiple
    excel_names (all ignored) can each match independently."""

    def __init__(self, factories: List[ColumnMappingFactory]):
        self._factories = factories

    def maps(self, column_name: str) -> bool:
        return any(f.maps(column_name) for f in self._factories)

    def create_mapping(self, origin: str, column_name: str):
        for f in self._factories:
            if f.maps(column_name):
                return f.create_mapping(origin, column_name)
        raise ValueError(f"No factory matches column: {column_name}")
