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
    synonyms: List[str]
    relations: List[Tuple[TermIdentifier, Any]]
    owl_property_type: OWLPropertyType
    sub_property_of: List[TermIdentifier]
    domain: Optional[TermIdentifier]
    range: Optional[TermIdentifier]
    origin: Tuple[str, int]

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)

    def __hash__(self) -> int:
        return hash(self.__dict__.values())


@dataclass
class UnresolvedRelation:
    id: Optional[str] = None
    label: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    relations: List[Tuple[TermIdentifier, Any]] = field(default_factory=list)

    sub_property_of: List[TermIdentifier] = field(default_factory=list)

    owl_property_type: Optional[OWLPropertyType] = None
    domain: Optional[TermIdentifier] = None
    range: Optional[TermIdentifier] = None
    origin: Optional[Tuple[str, int]] = None

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

    def __hash__(self) -> int:
        fields = [
            self.id,
            self.label,
            sum(map(hash, self.synonyms)),
            sum(map(hash, self.relations)),
            sum(map(hash, self.sub_property_of)),
            self.owl_property_type,
            self.domain,
            self.range
        ]
        return sum(map(hash, fields))
