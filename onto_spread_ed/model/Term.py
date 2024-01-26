from dataclasses import dataclass, field
from typing import Any, Optional, Union, List, Tuple

from typing_extensions import Self

from .TermIdentifier import TermIdentifier


@dataclass
class Term:
    id: str
    label: str
    synonyms: List[str]
    origin: Tuple[str, int]
    relations: List[Tuple[TermIdentifier, Any]]
    sub_class_of: List[TermIdentifier]
    equivalent_to: List[str]
    disjoint_with: List[TermIdentifier]

    def identifier(self) -> TermIdentifier:
        return TermIdentifier(self.id, self.label)


@dataclass
class UnresolvedTerm:
    id: Optional[str] = None
    label: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    origin: Optional[Tuple[str, int]] = None
    relations: List[Tuple[TermIdentifier, Any]] = field(default_factory=list)
    sub_class_of: List[TermIdentifier] = field(default_factory=list)
    equivalent_to: List[str] = field(default_factory=list)
    disjoint_with: List[TermIdentifier] = field(default_factory=list)

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
