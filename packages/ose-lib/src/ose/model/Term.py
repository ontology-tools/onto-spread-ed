import abc
import typing
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Sequence, Union, List, Tuple, Self, overload

from .TermIdentifier import (
    TermIdentifierBase,
    TermIdentifier,
    UnresolvedTermIdentifier,
    termid,
)


class TermBase(abc.ABC, TermIdentifierBase):
    relations: Sequence[Tuple[TermIdentifierBase, Any]]
    sub_class_of: Sequence[TermIdentifierBase]
    equivalent_to: List[str]
    disjoint_with: Sequence[TermIdentifierBase]

    origin: Tuple[str, int] | None

    @overload
    def identifier(self) -> UnresolvedTermIdentifier: ...
    @overload
    def identifier[T: TermIdentifierBase](self, cls: type[T]) -> T: ...
    def identifier(self, cls: type | None = None) -> TermIdentifierBase:
        t = UnresolvedTermIdentifier(self.id, self.label)
        return t if cls is None else t._assert_cast(cls)

    def curation_status(self) -> typing.Optional[str]:
        """
        Convenience function to retrieve the value of the annotation property 'has curation status' (IAO:0000114)

        :return: The curation status if defined.
        """
        return next(
            (v.strip() for r, v in self.relations if r.id == "IAO:0000114"), None
        )

    def definition(self, value: Optional[str] = None) -> typing.Optional[str]:
        """
        Convenience function to retrieve or set the value of the annotation property 'has curation status' (IAO:0000114)

        :return: The curation status if defined.
        """
        i, v = next(
            (
                (i, v.strip())
                for i, (r, v) in enumerate(self.relations)
                if r.id == "IAO:0000115"
            ),
            (None, None),
        )

        if value is None or v == value:
            return v

        r = termid(id="IAO:0000115", label="definition")
        self.relations = list(self.relations)
        if i is not None:
            self.relations[i] = (r, value)
        else:
            self.relations.append((r, value))

        return value

    def synonyms(self) -> List[str]:
        """
        Convenience function to retrieve the values of the annotation property 'alternative label' (IAO:0000118)

        :return: All defined synonyms.
        """
        return [v.strip() for r, v in self.relations if r.id == "IAO:0000118"]

    def is_external(self) -> Optional[bool]:
        curation_status = self.curation_status()
        if curation_status is None:
            return None

        return curation_status in ["External"]

    def get_relation_value(self, id: TermIdentifier) -> Optional[Any]:
        return next(iter(self.get_relation_values(id)), None)

    def get_relation_values(self, id: TermIdentifier) -> List[Any]:
        return [
            v
            for r, v in self.relations
            if (
                (id.id is None or id.id == r.id)
                and id.label is None
                or id.label == r.label
            )
        ]

    def __eq__(self, other):
        if other is None or not isinstance(other, Term):
            return False

        return all(
            [
                self.id == other.id,
                self.label == other.label,
                sorted(self.sub_class_of) == sorted(other.sub_class_of),
                sorted(self.equivalent_to) == sorted(other.equivalent_to),
                sorted(self.disjoint_with) == sorted(other.disjoint_with),
                sorted(self.relations) == sorted(other.relations),
            ]
        )

    def __hash__(self):
        return sum(
            hash(x)
            for x in [
                self.id,
                self.label,
                self.origin,
                sum(hash(y) for y in self.sub_class_of),
                sum(hash(y) for y in self.equivalent_to),
                sum(hash(y) for y in self.disjoint_with),
                sum(hash(y) for y in self.relations),
            ]
        )


@dataclass
class Term(TermBase):
    id: str
    label: str
    origin: Tuple[str, int]
    relations: List[Tuple[TermIdentifier, Any]]
    sub_class_of: List[TermIdentifier]
    equivalent_to: List[str]
    disjoint_with: List[TermIdentifier]


@dataclass
class UnresolvedTerm(TermBase):
    id: Optional[str] = None
    label: Optional[str] = None
    origin: Optional[Tuple[str, int]] = None
    relations: List[Tuple[TermIdentifierBase, TermIdentifierBase | str]] = field(default_factory=list)
    sub_class_of: List[TermIdentifierBase] = field(default_factory=list)
    equivalent_to: List[str] = field(default_factory=list)
    disjoint_with: List[TermIdentifierBase] = field(default_factory=list)

    def is_unresolved(self) -> bool:
        relation_values = [
            x for r, x in self.relations if isinstance(x, TermIdentifier)
        ]
        return (
            any(v is None for v in [self.id, self.label, self.origin])
            or len(self.disjoint_with) + len(self.sub_class_of) + len(relation_values)
            > 0
            and any(
                t.is_unresolved()
                for t in [*self.sub_class_of, *self.disjoint_with, *relation_values]
            )
        )

    def is_resolved(self) -> bool:
        return not self.is_unresolved()

    def as_resolved_term(self) -> Term | None:
        if self.is_unresolved():
            return None
        else:
            return Term(**self.__dict__)

    def __hash__(self):
        return super().__hash__()
