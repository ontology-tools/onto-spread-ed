import abc
import enum
import re
from dataclasses import dataclass
from typing import Optional, Callable, Union, Any, List, Tuple

from .Relation import Relation, OWLPropertyType
from .TermIdentifier import TermIdentifier


class ColumnMappingKind(enum.Enum):
    INVERSE_OF = 17
    IGNORE = 16
    RELATION_TYPE = 15
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


class ColumnMapping(abc.ABC):

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


@dataclass
class ChoiceColumnMapping(SimpleColumnMapping):
    choices: List[str]

    def valid(self, value: str) -> bool:
        return value is not None and (value.strip() in self.choices)


class PrefixColumnMapping(SimpleColumnMapping):
    _pattern = re.compile(r'"([\w\d]+):(.*)"')

    def __init__(self, name: str, separator: Optional[str] = None):
        self.name = name
        self.separator = separator
        self.kind = ColumnMappingKind.PREFIX

    def get_value(self, value: str) -> List[Tuple[str, str]]:
        values = [value]
        if self.separator is not None:
            values = value.split(self.separator)

        res: List[Tuple[str, str]] = []
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
    _pattern = re.compile(r"^([^\[]+)(?:\[(\w+:\d+)\]|\((\w+:\d+)\))?$")

    def get_value(self, value: str) -> TermIdentifier:
        match = self._pattern.match(value.strip())
        id = match.group(2)
        label = match.group(1)
        return TermIdentifier(id=id.strip() if id is not None else None,
                              label=label.strip() if label is not None else None)

    def valid(self, value: str) -> bool:
        return self._pattern.match(value.strip()) is not None


@dataclass
class ManchesterSyntaxMapping(SimpleColumnMapping):
    pass


@dataclass
class TermMapping(SimpleColumnMapping):
    require_id: Optional[bool] = False
    require_label: Optional[bool] = False
    separator: Optional[str] = None

    _term_pattern = re.compile(r"^([^\[]*)\s*(?:\[(.*)\])?$")

    def get_value(self, value: str) -> List[TermIdentifier]:
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
            m = self._term_pattern.match(v.strip())
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

    def get_synonyms(self, value: str) -> List[str]:
        match = re.match(self._label_pattern, value)
        if match is None:
            return []
        else:
            return [s.strip() for s in match.group(2).split(";")]

    def valid(self, value: str) -> bool:
        return self._label_pattern.match(value) is not None


@dataclass
class RelationColumnMapping(ColumnMapping):
    relation: Relation
    name: str
    separator: Optional[str] = None

    def get_name(self) -> str:
        return self.name

    def get_kind(self) -> ColumnMappingKind:
        return ColumnMappingKind.RELATION

    def get_relation(self) -> Relation:
        return self.relation

    def get_value(self, value: str) -> List[Tuple[TermIdentifier, Any]]:
        values = [x.strip() for x in str(value).split(self.separator)] if self.separator is not None else [
            str(value).strip()]

        if self.relation.owl_property_type == OWLPropertyType.ObjectProperty:
            values = [TermIdentifier(label=x) for x in values]

        return [(self.relation.identifier(), x) for x in values]


class ColumnMappingFactory(abc.ABC):
    @abc.abstractmethod
    def maps(self, column_name: str) -> bool:
        pass

    @abc.abstractmethod
    def create_mapping(self, origin: str, column_name: str) -> ColumnMapping:
        pass


@dataclass
class SingletonMappingFactory(ColumnMappingFactory):
    column_names: List[str]
    mapping: ColumnMapping

    def maps(self, column_name: str) -> bool:
        return column_name in self.column_names

    def create_mapping(self, origin: str, column_name: str) -> ColumnMapping:
        return self.mapping


@dataclass
class PatternMappingFactory(ColumnMappingFactory):
    pattern: re.Pattern
    mapping_factory: Callable[[str, str, re.Match], ColumnMapping]

    def maps(self, column_name: str) -> bool:
        return re.match(self.pattern, column_name) is not None

    def create_mapping(self, origin: str, column_name: str) -> ColumnMapping:
        match = re.match(self.pattern, column_name)
        return self.mapping_factory(origin, column_name, match)


def singleton(excel_names: List[str], mapping: Callable[..., ColumnMapping], *args, **kwargs) -> ColumnMappingFactory:
    return SingletonMappingFactory(excel_names, mapping(*args, **{"name": excel_names[0], **kwargs}))


def simple(excel_names: List[str], kind: ColumnMappingKind, name: Optional[str] = None) -> ColumnMappingFactory:
    return SingletonMappingFactory(excel_names, SimpleColumnMapping(kind, excel_names[0] if name is None else name))


def relation(excel_name: List[str], relation: TermIdentifier, name: Optional[str] = None,
             separator: Optional[str] = None,
             property_type: OWLPropertyType = OWLPropertyType.AnnotationProperty) -> ColumnMappingFactory:
    return SingletonMappingFactory(excel_name, RelationColumnMapping(
        Relation(relation.id, relation.label, [], [], property_type, [], None, None, [], ("<schema>", 0)),
        excel_name[0] if name is None else name, separator))


def internal(excel_names: List[str], name: str, split: Optional[str] = None) -> ColumnMappingFactory:
    return relation(excel_names, TermIdentifier(id=None, label=name), name, split, OWLPropertyType.Internal)


def ignore(excel_name: str) -> ColumnMappingFactory:
    def _ignore(*_args, **_kwargs):
        return SimpleColumnMapping(ColumnMappingKind.IGNORE, excel_name)

    return singleton([excel_name], _ignore)


def relation_pattern(pattern: Union[str, re.Pattern],
                     factory: Callable[[str, re.Match], TermIdentifier],
                     separator: Optional[str] = None,
                     relation_kind: OWLPropertyType = OWLPropertyType.AnnotationProperty) -> ColumnMappingFactory:
    def f(origin: str, rel_name: str, match: re.Match) -> RelationColumnMapping:
        identifier = factory(rel_name, match)
        return RelationColumnMapping(
            Relation(identifier.id, identifier.label, [], [], relation_kind, [], None, None, [], (origin, 0)),
            f"REL {rel_name}",
            separator
        )

    return PatternMappingFactory(pattern, f)
