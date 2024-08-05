import enum
from dataclasses import dataclass, field
from typing import Optional, Any, Tuple, List

from .TermIdentifier import TermIdentifier


class OWLPropertyType(enum.Enum):
    IDProperty = 0
    AnnotationProperty = 1
    DataProperty = 2
    ObjectProperty = 3
    Internal = 4
    "Only internal usage. Do not expose to OWL"

    def __json__(self):
        return self.name


@dataclass
class Relation:
    id: str
    label: str
    equivalent_relations: List[TermIdentifier]
    relations: List[Tuple[TermIdentifier, Any]]
    owl_property_type: OWLPropertyType
    sub_property_of: List[TermIdentifier]
    domain: Optional[TermIdentifier]
    range: Optional[TermIdentifier]
    inverse_of: List[TermIdentifier]
    origin: Tuple[str, int]

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)

    def __hash__(self) -> int:
        return hash(self.__dict__.values())


@dataclass
class UnresolvedRelation:
    id: Optional[str] = None
    label: Optional[str] = None
    equivalent_relations: List[TermIdentifier] = field(default_factory=list)
    relations: List[Tuple[TermIdentifier, Any]] = field(default_factory=list)
    inverse_of: List[TermIdentifier] = field(default_factory=list)

    sub_property_of: List[TermIdentifier] = field(default_factory=list)

    owl_property_type: Optional[OWLPropertyType] = None
    domain: Optional[TermIdentifier] = None
    range: Optional[TermIdentifier] = None
    origin: Optional[Tuple[str, int]] = None

    def is_unresolved(self) -> bool:
        relation_values = [x for r, x in self.relations if isinstance(x, TermIdentifier)]
        return any(v is None for v in [self.id, self.label, self.owl_property_type, self.origin]) or \
            self.domain is not None and self.domain.is_unresolved() or \
            self.range is not None and self.range.is_unresolved() or \
            len(self.sub_property_of) + len(relation_values) + len(self.equivalent_relations) > 0 and \
            any(t.is_unresolved() for t in
                [*self.sub_property_of, *relation_values, *self.equivalent_relations, *self.inverse_of])

    def to_resolved(self) -> Optional[Relation]:
        if self.is_unresolved():
            return None
        else:
            return Relation(**self.__dict__)

    def as_resolved(self) -> Relation:
        if self.is_unresolved():
            raise ValueError(f"Cannot convert unresolved term {self} to a resolved term.")

        return Relation(**self.__dict__)

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)

    def __hash__(self) -> int:
        fields = [
            self.id,
            self.label,
            sum(map(hash, self.equivalent_relations)),
            sum(map(hash, self.relations)),
            sum(map(hash, self.sub_property_of)),
            sum(map(hash, self.inverse_of)),
            self.owl_property_type,
            self.domain,
            self.range
        ]
        return sum(map(hash, fields))
