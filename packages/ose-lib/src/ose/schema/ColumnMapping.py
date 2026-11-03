import enum
import re
from typing import Annotated, Any, ClassVar, List, Literal, Optional, Self, Tuple, Union
from urllib.parse import urlparse

from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer, PrivateAttr, model_validator

from ose.schema.Relation import OWLPropertyType, UnresolvedRelation
from ose.schema.TermIdentifier import TermIdentifier, UnresolvedTermIdentifier


class ColumnMappingKind(enum.Enum):
    EXCLUDED_IMPORT_ID = 20
    VERSION_IRI = 19
    INVERSE_OF = 18
    IGNORE = 17
    RELATION_TYPE = 16
    PREFIX = 15
    PLAIN = 14
    IMPORTED_ID = 13
    ROOT_ID = 12
    ONTOLOGY_IRI = 11
    RANGE = 10
    DOMAIN = 9
    ONTOLOGY_ID = 8
    SUB_PROPERTY_OF = 7
    SYNONYMS = 6
    RELATION = 5
    DISJOINT_WITH = 4
    EQUIVALENT_TO = 3
    SUB_CLASS_OF = 2
    LABEL = 1
    ID = 0


def _enum_by_name(e: type[enum.Enum]) -> tuple[BeforeValidator, PlainSerializer]:
    """Read and write enum members by their name, e.g. "SUB_CLASS_OF" or "ObjectProperty", instead of their value"""
    return (
        BeforeValidator(lambda v: e.__members__.get(v, v) if isinstance(v, str) else v),
        PlainSerializer(lambda v: v.name, return_type=str),
    )


Kind = Annotated[ColumnMappingKind, *_enum_by_name(ColumnMappingKind)]
PropertyType = Annotated[OWLPropertyType, *_enum_by_name(OWLPropertyType)]


class ColumnMapping(BaseModel):
    """
    Describes how the values of a spreadsheet column are interpreted.

    A mapping applies to all columns whose header is listed in `columns` or fully matches `pattern`.
    """

    kind: Kind
    columns: List[str] = []
    pattern: Optional[re.Pattern[str]] = None

    _name: Optional[str] = PrivateAttr(default=None)
    _origin: str = PrivateAttr(default="<schema>")

    @model_validator(mode="after")
    def _check_matches_something(self) -> "ColumnMapping":
        if not self.columns and self.pattern is None:
            raise ValueError("A column mapping needs `columns` or a `pattern`")
        return self

    def match(self, header: str) -> Optional[re.Match[str] | bool]:
        if header in self.columns:
            return True
        if self.pattern is not None:
            return self.pattern.fullmatch(header)
        return None

    def for_column(self, origin: str, header: str, match: re.Match[str] | bool) -> Self:
        """Returns the mapping as applied to a concrete column"""
        mapping = self.model_copy()
        mapping._name = header
        mapping._origin = origin
        return mapping

    def get_name(self) -> str:
        return self._name if self._name is not None else (self.columns[0] if self.columns else str(self.pattern))

    def get_kind(self) -> ColumnMappingKind:
        return self.kind

    def get_value(self, value: str) -> Any:
        return value.strip()

    def valid(self, value: str) -> bool:
        return True


class SimpleColumnMapping(ColumnMapping):
    type: Literal["plain"] = "plain"


class ChoiceColumnMapping(ColumnMapping):
    type: Literal["choice"] = "choice"
    choices: List[str]

    def valid(self, value: str) -> bool:
        return value is not None and (value.strip() in self.choices)


class PrefixColumnMapping(ColumnMapping):
    type: Literal["prefix"] = "prefix"
    kind: Kind = ColumnMappingKind.PREFIX
    separator: Optional[str] = None

    _pattern: ClassVar[re.Pattern[str]] = re.compile(r'"([\w\d]+):(.*)"')

    def _values(self, value: str) -> List[str]:
        return [v.strip() for v in (value.split(self.separator) if self.separator is not None else [value])]

    def get_value(self, value: str) -> List[Tuple[str, str]]:
        res: List[Tuple[str, str]] = []
        for v in self._values(value):
            m = self._pattern.match(v)

            if m is None:
                raise ValueError(
                    f"Value '{v}' does not match the expected prefix pattern. `valid` must be checked first."
                )

            res.append((m.group(1).strip(), m.group(2).strip()))

        return res

    def valid(self, value: str) -> bool:
        return all(self._pattern.match(v) is not None for v in self._values(value))


class ParentMapping(ColumnMapping):
    type: Literal["parent"] = "parent"
    kind: Kind = ColumnMappingKind.SUB_CLASS_OF

    _pattern: ClassVar[re.Pattern[str]] = re.compile(r"^([^\[]+)(?:\[(\w+:\d+)\]|\((\w+:\d+)\))?$")

    def get_value(self, value: str) -> UnresolvedTermIdentifier:
        match = self._pattern.match(value.strip())

        if match is None:
            raise ValueError(
                f"Value '{value}' does not match the expected prefix pattern. `valid` must be checked first."
            )

        id = match.group(2)
        label = match.group(1)
        return UnresolvedTermIdentifier(
            id=id.strip() if id is not None else None,
            label=label.strip() if label is not None else None,
        )

    def valid(self, value: str) -> bool:
        return self._pattern.match(value.strip()) is not None


class ManchesterSyntaxMapping(ColumnMapping):
    type: Literal["manchester"] = "manchester"
    kind: Kind = ColumnMappingKind.EQUIVALENT_TO


class IRIMapping(ColumnMapping):
    type: Literal["iri"] = "iri"

    def valid(self, value: str) -> bool:
        return urlparse(value.strip()).scheme != ""


class TermMapping(ColumnMapping):
    type: Literal["term"] = "term"
    require_id: bool = False
    require_label: bool = False
    separator: Optional[str] = None

    _term_pattern: ClassVar[re.Pattern[str]] = re.compile(r"^([^\[]*)\s*(?:\[(.*)\])?$")

    def get_value(self, value: str) -> List[UnresolvedTermIdentifier]:
        idents = []
        for val in [value.strip()] if self.separator is None else value.strip().split(self.separator):
            if val.strip() == "":
                continue

            m = self._term_pattern.match(val.strip())

            if m is None:
                raise ValueError(
                    f"Value '{val}' does not match the expected prefix pattern. `valid` must be checked first."
                )

            label = m.group(1)
            id = m.group(2)
            idents.append(
                UnresolvedTermIdentifier(
                    id=None if id is None else id.strip(),
                    label=None if label is None else label.strip(),
                )
            )

        return idents

    def valid(self, value: str) -> bool:
        if self.separator is None:
            values = [value]
        else:
            values = value.strip().split(self.separator)

        values = [v.strip() for v in values if v.strip() != ""]

        for v in values:
            m = self._term_pattern.match(v.strip())
            if m is None or m.group(1) is None and self.require_label or m.group(2) is None and self.require_id:
                return False

        return True


class LabelMapping(ColumnMapping):
    type: Literal["label"] = "label"
    kind: Kind = ColumnMappingKind.LABEL


class RelationRef(BaseModel):
    """
    The relation a column holds values for. For mappings with a `pattern`, `id` and `label` may reference the
    groups of the match, e.g. `{1}` for the first group.
    """

    id: Optional[str] = None
    label: str


class RelationColumnMapping(ColumnMapping):
    type: Literal["relation"] = "relation"
    kind: Kind = ColumnMappingKind.RELATION
    relation: RelationRef
    property_type: PropertyType = OWLPropertyType.AnnotationProperty
    separator: Optional[str] = None

    def for_column(self, origin: str, header: str, match: re.Match[str] | bool) -> Self:
        mapping = super().for_column(origin, header, match)
        if isinstance(match, re.Match):
            groups = [match.group(0), *match.groups()]
            mapping.relation = RelationRef(
                id=self.relation.id.format(*groups) if self.relation.id is not None else None,
                label=self.relation.label.format(*groups),
            )
        return mapping

    def relation_identifier(self) -> TermIdentifier:
        return TermIdentifier(id=self.relation.id, label=self.relation.label)  # type: ignore[arg-type]

    def as_unresolved_relation(self) -> UnresolvedRelation:
        return UnresolvedRelation(
            id=self.relation.id,
            label=self.relation.label,
            owl_property_type=self.property_type,
            origin=(self._origin, 0),
        )

    def get_value(self, value: str) -> List[Tuple[TermIdentifier, str | UnresolvedTermIdentifier]]:
        plain_values = (
            [x.strip() for x in str(value).split(self.separator)]
            if self.separator is not None
            else [str(value).strip()]
        )

        values: List[str | UnresolvedTermIdentifier]
        if self.property_type == OWLPropertyType.ObjectProperty:
            values = [UnresolvedTermIdentifier(label=x) for x in plain_values]
        else:
            values = list(plain_values)

        identifier = self.relation_identifier()
        return [(identifier, x) for x in values]


AnyColumnMapping = Annotated[
    Union[
        SimpleColumnMapping,
        ChoiceColumnMapping,
        PrefixColumnMapping,
        ParentMapping,
        ManchesterSyntaxMapping,
        IRIMapping,
        TermMapping,
        LabelMapping,
        RelationColumnMapping,
    ],
    Field(discriminator="type"),
]
"""Any column mapping, distinguished by its `type` when read from JSON"""
