from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar, Generic, Any, Optional, Callable

A = TypeVar("A")
B = TypeVar("B")

Message = dict[str, Any]


@dataclass
class Result(Generic[A]):
    value: Optional[A] = None
    template: Message = field(default_factory=dict)
    errors: list[Message] = field(default_factory=list)
    warnings: list[Message] = field(default_factory=list)

    def error(self, **kwargs) -> None:
        self.errors.append({**self.template, **kwargs})

    def warning(self, **kwargs) -> None:
        self.warnings.append({**self.template, **kwargs})

    def bind(self, fn: Callable[[A], Result[B]]) -> Result[B]:
        if self.value is None:
            return Result(template=self.template, errors=self.errors, warnings=self.warnings, value=self.value)
        else:
            return self.merge(fn(self.value))

    def merge(self, other: Result[B]) -> Result[B]:
        return Result(template={**self.template, **other.template},
                      errors=self.errors + other.errors,
                      warnings=self.warnings + other.errors,
                      value=other.value)

    def ok(self) -> bool:
        return self.value is not None
