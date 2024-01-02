import enum
from dataclasses import dataclass, field
from typing import Optional, Any

from .TermIdentifier import TermIdentifier


class OWLPropertyType(enum.Enum):
    IDProperty = 0
    AnnotationProperty = 1
    DataProperty = 2
    ObjectProperty = 3


@dataclass
class Relation:
    id: str
    label: str
    synonyms: list[str]
    relations: list[tuple[TermIdentifier, Any]]
    owl_property_type: OWLPropertyType
    sub_property_of: list[TermIdentifier]
    domain: Optional[TermIdentifier]
    range: Optional[TermIdentifier]
    origin: tuple[str, int]

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)

    def __hash__(self) -> int:
        return hash(self.__dict__.values())


@dataclass
class UnresolvedRelation:
    id: Optional[str] = None
    label: Optional[str] = None
    synonyms: list[str] = field(default_factory=list)
    relations: list[tuple[TermIdentifier, Any]] = field(default_factory=list)

    sub_property_of: list[TermIdentifier] = field(default_factory=list)

    owl_property_type: Optional[OWLPropertyType] = None
    domain: Optional[TermIdentifier] = None
    range: Optional[TermIdentifier] = None
    origin: Optional[tuple[str, int]] = None

    def is_unresolved(self) -> bool:
        return any(v is None for v in [self.id, self.label, self.owl_property_type, self.origin])

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


