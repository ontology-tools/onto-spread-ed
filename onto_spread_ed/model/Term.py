from dataclasses import dataclass, field
from typing import Any, Optional, Union

from typing_extensions import Self

from .Relation import Relation, UnresolvedRelation
from .TermIdentifier import TermIdentifier


@dataclass
class Term:
    id: str
    label: str
    synonyms: list[str]
    origin: tuple[str, int]
    relations: list[tuple[TermIdentifier, Any]]
    sub_class_of: list[TermIdentifier]
    equivalent_to: list[str]
    disjoint_with: list[TermIdentifier]

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)


@dataclass
class UnresolvedTerm:
    id: Optional[str] = None
    label: Optional[str] = None
    synonyms: list[str] = field(default_factory=list)
    origin: Optional[tuple[str, int]] = None
    relations: list[tuple[TermIdentifier, Any]] = field(default_factory=list)
    sub_class_of: list[TermIdentifier] = field(default_factory=list)
    equivalent_to: list[str] = field(default_factory=list)
    disjoint_with: list[TermIdentifier] = field(default_factory=list)

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)

    def is_unresolved(self) -> bool:
        relation_values = [x for r, x in self.relations if isinstance(x, TermIdentifier)]
        return any(v is None for v in [self.id, self.label, self.origin]) or \
            len(self.disjoint_with) + len(self.sub_class_of) + len(relation_values) > 0 and \
            any(t.is_unresolved() for t in [*self.sub_class_of, *self.disjoint_with, *relation_values])

    def to_resolved(self) -> Optional[Term]:
        if self.is_unresolved():
            return None
        else:
            return Term(**self.__dict__)

    def as_resolved(self) -> Term:
        if self.is_unresolved():
            raise ValueError(f"Cannot convert unresolved term {self} to a resolved term.")

        return Term(**self.__dict__)

    def complement(self, other: Union[Self, Term, TermIdentifier]) -> None:
        for k in self.__dict__.keys():
            if k not in other.__dict__:
                continue

            if self.__dict__[k] is None:
                self.__dict__[k] = other.__dict__[k]
            elif other.__dict__[k] is not None and isinstance(other.__dict__[k], list):
                self.__dict__[k] += other.__dict__[k]
