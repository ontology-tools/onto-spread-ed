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
