from dataclasses import dataclass
from typing import Optional

from typing_extensions import Self


@dataclass
class TermIdentifier:
    id: Optional[str] = None
    label: Optional[str] = None

    def is_unresolved(self) -> bool:
        return self.id is None or self.label is None

    def complement(self, other: Self) -> None:
        if self.id is None:
            self.id = other.id

        if self.label is None:
            self.label = other.label

    def __json__(self) -> dict:
        return self.__dict__

    def __eq__(self, other):
        if other is None or not isinstance(other, TermIdentifier):
            return False

        return all([
            self.id == other.id,
            self.label == other.label
        ])

    def __hash__(self):
        return hash(self.id) + hash(self.label)

    def __lt__(self, other):
        if other is None or not isinstance(other, TermIdentifier):
            return False

        if self.id is None:
            return True

        if other.id is None:
            return False

        return self.id < other.id

