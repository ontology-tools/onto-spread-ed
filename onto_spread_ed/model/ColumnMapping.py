import abc
import enum
import re
from dataclasses import dataclass
from typing import Optional, Callable, Union, Any

from .TermIdentifier import TermIdentifier


class ColumnMappingKind(enum.Enum):
    PREFIX = 14
    PLAIN = 13
    IMPORTED_ID = 12
    ROOT_ID = 11
    PURL = 10
    ONTOLOGY_ID = 8
    SUB_PROPERTY_OF = 7
    ID = 0
    LABEL = 1
    SUB_CLASS_OF = 2
    EQUIVALENT_TO = 3
    DISJOINT_WITH = 4
    RELATION = 5
    SYNONYMS = 6
    DOMAIN = 8
    RANGE = 9


class ColumnMapping:

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    def get_kind(self) -> ColumnMappingKind:
        pass

    def get_value(self, value: str) -> Any:
        return value.strip()

    def valid(self, value: str) -> bool:
        return True


@dataclass
class SimpleColumnMapping(ColumnMapping):
    kind: ColumnMappingKind
    name: str

    def get_name(self) -> str:
        return self.name

    def get_kind(self) -> ColumnMappingKind:
        return self.kind


class PrefixColumnMapping(SimpleColumnMapping):
    _pattern = re.compile(r'"([\w\d]+):(.*)"')

    def __init__(self, name: str, separator: Optional[str] = None):
        self.name = name
        self.separator = separator
        self.kind = ColumnMappingKind.PREFIX

    def get_value(self, value: str) -> list[tuple[str, str]]:
        values = [value]
        if self.separator is not None:
            values = value.split(self.separator)

        res: list[tuple[str, str]] = []
        for v in values:
            m = self._pattern.match(v.strip())
            res.append((m.group(1).strip(), m.group(2).strip()))

        return res

    def valid(self, value: str) -> bool:
        values = [value]
        if self.separator is not None:
            values = value.split(self.separator)

        return all(self._pattern.match(v) is not None for v in values)


@dataclass
class ParentMapping(SimpleColumnMapping):
    _pattern = re.compile(r"^([\w\s]+)(?:\[(\w+:\d+)\]|\((\w+:\d+)\))?$")

    def get_value(self, value: str) -> TermIdentifier:
        match = self._pattern.match(value.strip())
        return TermIdentifier(id=match.group(2), label=match.group(1))

    def valid(self, value: str) -> bool:
        return self._pattern.match(value.strip()) is not None


@dataclass
class TermMapping(SimpleColumnMapping):
    require_id: Optional[bool] = False
    require_label: Optional[bool] = False
    separator: Optional[str] = None

    _term_pattern = re.compile(r"(.*\s+)?(?:\[(.*)\])?")

    def get_value(self, value: str) -> list[TermIdentifier]:
        idents = []
        for val in [value.strip()] if self.separator is None else value.strip().split(self.separator):
            m = self._term_pattern.match(val.strip())
            label = m.group(1)
            id = m.group(2)
            idents.append(TermIdentifier(
                id=None if id is None else id.strip(),
                label=None if label is None else label.strip()))

        return idents

    def valid(self, value: str) -> bool:
        values = [value]
        if self.separator is not None:
            values = value.strip().split(self.separator)

        for v in values:
            m = self._term_pattern.match(value.strip())
            if m is None or m.group(1) is None and self.require_label or m.group(2) is None and self.require_id:
                return False

        return True


@dataclass
class LabelMapping(SimpleColumnMapping):
    kind = ColumnMappingKind.LABEL

    _label_pattern = re.compile(r"(.*)\s*(?:\((.*)\))?")

    def __init__(self, name: str):
        self.name = name

    def get_kind(self) -> ColumnMappingKind:
        return ColumnMappingKind.LABEL

    def get_value(self, value: str) -> str:
        return self.get_label(value)

    def get_label(self, value: str) -> str:
        match = re.match(self._label_pattern, value)
        if match is None:
            return value.strip()
        else:
            return match.group(1).strip()

    def get_synonyms(self, value: str) -> list[str]:
        match = re.match(self._label_pattern, value)
        if match is None:
            return []
        else:
            return [s.strip() for s in match.group(2).split(";")]

    def valid(self, value: str) -> bool:
        return self._label_pattern.match(value) is not None


@dataclass
class RelationColumnMapping(ColumnMapping):
    relation: TermIdentifier
    name: str
    separator: Optional[str] = None

    def get_name(self) -> str:
        return self.name

    def get_kind(self) -> ColumnMappingKind:
        return ColumnMappingKind.RELATION

    def get_relation(self) -> TermIdentifier:
        return self.relation

    def get_value(self, value: str) -> list[tuple[TermIdentifier, Any]]:
        if self.separator is None:
            return [(self.relation, value.strip())]
        else:
            return [(self.relation, x.strip()) for x in value.split(self.separator)]


class ColumnMappingFactory:
    @abc.abstractmethod
    def maps(self, column_name: str) -> bool:
        pass

    @abc.abstractmethod
    def create_mapping(self, column_name: str) -> ColumnMapping:
        pass


@dataclass
class SingletonMappingFactory(ColumnMappingFactory):
    column_names: list[str]
    mapping: ColumnMapping

    def maps(self, column_name: str) -> bool:
        return column_name in self.column_names

    def create_mapping(self, column_name: str) -> ColumnMapping:
        return self.mapping


@dataclass
class PatternMappingFactory(ColumnMappingFactory):
    pattern: re.Pattern
    mapping_factory: Callable[[str, re.Match], ColumnMapping]

    def maps(self, column_name: str) -> bool:
        return re.match(self.pattern, column_name) is not None

    def create_mapping(self, column_name: str) -> ColumnMapping:
        match = re.match(self.pattern, column_name)
        return self.mapping_factory(column_name, match)


class Schema:
    _mapping_factories: list[ColumnMappingFactory]

    def __init__(self, mapping_factories: list[ColumnMappingFactory]):
        self._mapping_factories = mapping_factories

    def get_mapping(self, header_name: str) -> Optional[ColumnMapping]:
        return next(
            iter(m.create_mapping(header_name) for m in self._mapping_factories if m.maps(header_name)), None)


def singleton(excel_names: list[str], mapping: Callable[[...], ColumnMapping], *args, **kwargs) -> ColumnMappingFactory:
    return SingletonMappingFactory(excel_names, mapping(*args, **{"name": excel_names[0], **kwargs}))


def simple(excel_names: list[str], kind: ColumnMappingKind, name: Optional[str] = None) -> ColumnMappingFactory:
    return SingletonMappingFactory(excel_names, SimpleColumnMapping(kind, excel_names[0] if name is None else name))


def relation(excel_name: list[str], relation: TermIdentifier, name: Optional[str] = None,
             split: Optional[str] = None) -> ColumnMappingFactory:
    return SingletonMappingFactory(excel_name,
                                   RelationColumnMapping(relation, excel_name[0] if name is None else name, split))


def relation_pattern(pattern: Union[str, re.Pattern],
                     factory: Callable[[str, re.Match], TermIdentifier]) -> ColumnMappingFactory:
    return PatternMappingFactory(pattern, lambda rel_name, match: RelationColumnMapping(
        factory(rel_name, match),
        f"REL {rel_name}"))


DEFAULT_MAPPINGS = [
    simple(["ID", "BCIO_ID"], ColumnMappingKind.ID),
    simple(["Domain"], ColumnMappingKind.DOMAIN),
    simple(["Range"], ColumnMappingKind.RANGE),
    singleton(["Name", "Label", "Label (synonym)", "Relationship"], LabelMapping),
    singleton(["Parent", "Parent class/ BFO class"], ParentMapping, kind=ColumnMappingKind.SUB_CLASS_OF),
    singleton(["Parent relationship"], ParentMapping, kind=ColumnMappingKind.SUB_PROPERTY_OF),
    simple(["Logical definition", "Equivalent to relationship"], ColumnMappingKind.EQUIVALENT_TO),
    simple(["Disjoint classes"], ColumnMappingKind.DISJOINT_WITH),
    relation(["Definition"], TermIdentifier(id="IAO:0000115", label="definition")),
    relation(["Definition_ID"], TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy")),
    relation(["Definition_Source"], TermIdentifier(id="IAO:0000119", label="definition source")),
    relation(["Examples", "Examples of usage", "Elaboration"], TermIdentifier(id="IAO:0000112", label="example of usage")),
    relation(["Curator note"], TermIdentifier(id="IAO:0000232", label="curator note")),
    relation(["Synonyms"], TermIdentifier(id="IAO:0000118", label="alternative label"), ";"),
    relation(["Comment"], TermIdentifier(id="rdfs:comment", label="rdfs:comment")),
    relation(["Curation status"], TermIdentifier(id="IAO:0000114", label="has curation status")),
    relation_pattern(r"REL '([^'])+'", lambda name, match: TermIdentifier(label=match.group(1)))
]

DEFAULT_IMPORT_SCHEMA = Schema([
    simple(["Ontology ID"], ColumnMappingKind.ONTOLOGY_ID),
    simple(["PURL"], ColumnMappingKind.PURL),
    singleton(["ROOT ID"], TermMapping, kind=ColumnMappingKind.ROOT_ID, require_id=True, require_label=True),
    singleton(["IDs"], TermMapping, kind=ColumnMappingKind.IMPORTED_ID, require_id=True, require_label=True, separator=";"),
    simple(["Intermediates"], ColumnMappingKind.PLAIN),
    singleton(["Prefix"], PrefixColumnMapping, separator=";")

])

DEFAULT_SCHEMA = Schema(DEFAULT_MAPPINGS)
