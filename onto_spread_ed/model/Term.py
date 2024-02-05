import typing
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

    def curation_status(self) -> typing.Optional[str]:
        """
        Convenience function to retrieve the value of the annotation property 'has curation status' (IAO:0000114)

        :return: The curation status if defined.
        """
        return next((v.strip() for r, v in self.relations if r.id == "IAO:0000114"), None)

    def is_external(self) -> Optional[bool]:
        curation_status = self.curation_status()
        if curation_status is None:
            return None

        return curation_status in ["External"]

    def get_relation_value(self, id: TermIdentifier) -> Optional[Any]:
        return next((v for r, v in self.relations if ((id.id is None or id.id == r.id) and
                                                       id.label is None or id.label == r.label)), None)

    def __eq__(self, other):
        if other is None or not isinstance(other, Term):
            return False

        return all([
            self.id == other.id,
            self.label == other.label,
            sorted(self.synonyms) == sorted(other.synonyms),
            sorted(self.sub_class_of) == sorted(other.sub_class_of),
            sorted(self.equivalent_to) == sorted(other.equivalent_to),
            sorted(self.disjoint_with) == sorted(other.disjoint_with),
            sorted(self.relations) == sorted(other.relations),
        ])

    def __hash__(self):
        return sum(hash(x) for x in [
            self.id,
            self.label,
            self.origin,
            sorted(self.synonyms),
            sorted(self.sub_class_of),
            sorted(self.equivalent_to),
            sorted(self.disjoint_with),
            sorted(self.relations)
        ])


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
