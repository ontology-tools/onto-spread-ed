from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeIs, TypeVar, Generic, Any, Optional, Callable, Dict, cast, overload

A = TypeVar("A")
B = TypeVar("B")

Message = Dict[str, Any]


class _NOT_PROVIDED:
    pass


NOT_PROVIDED = _NOT_PROVIDED()


@dataclass
class Log:
    template: Message = field(default_factory=dict)
    errors: list[Message] = field(default_factory=list)
    warnings: list[Message] = field(default_factory=list)
    infos: list[Message] = field(default_factory=list)

    def __add__(self, other: Log | Result[tuple[()]]) -> Log:
        if isinstance(other, Result) and other.failed:
            raise ResultFailedException(other)
        
        if isinstance(other, Log):
            return self.merge(other)
        
        raise TypeError(f"Cannot add {type(other)} and Log")

    def error(self, **kwargs) -> None:
        self.errors.append({**self.template, **kwargs})

    def warning(self, **kwargs) -> None:
        self.warnings.append({**self.template, **kwargs})

    def info(self, **kwargs) -> None:
        self.infos.append({**self.template, **kwargs})

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def merge(self, other: Log) -> Log:
        return Log(
            template={**self.template, **other.template},
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            infos=self.infos + other.infos,
        )

    @overload
    def to_result(self) -> Result[tuple[()]]: ...
    @overload
    def to_result(self, value: A) -> Result[A]: ...
    def to_result(self, value: Any | _NOT_PROVIDED = NOT_PROVIDED) -> Result[Any]:
        if self.has_errors():
            return Err(self)
        else:
            return Success(value, self)
        
    def fail(self) -> Result:
        return Err(self)
    
class ResultFailedException(Exception):
    def __init__(self, result: Result):
        self.result = result
        super().__init__(f"Result failed with log: {result.log}")

class ResultContext():
    def __init__(self, log: Log | None = None):
        self.log = log if log is not None else Log()
        
    def __enter__(self) -> Log:
        return self.log

    def __exit__(self, exc_type, exc_value, traceback) -> Any:
        if exc_type is not None:
            if exc_type is not ResultFailedException:
                self.log.error(type="exception", message=traceback.format_exception(exc_type, exc_value, traceback))
            elif isinstance(exc_value, ResultFailedException) and self.log != exc_value.result.log:
                self.log += exc_value.result.log
                
            return True  # Suppress exception

class Result[A]:
    log: Log = field(default_factory=Log)

    @property
    def successful(self) -> bool:
        return isinstance(self, Success)
    
    @property
    def failed(self) -> bool:
        return isinstance(self, Err)

    def value_or_raise(self) -> A:
        if isinstance(self, Success):
            return self.value
        
        raise ResultFailedException(self)
        
    def map(self, func: Callable[[A], B]) -> Result[B]:
        if isinstance(self, Success):
            return Success(func(self.value), self.log)
        else:
            return cast(Result[B], self)
        
    def and_then(self, func: Callable[[A], Result[B]]) -> Result[B]:
        if isinstance(self, Success):
            new = func(self.value)
            new.log = self.log + new.log
            return new
        else:
            return cast(Result[B], self)
        
    def __and__(self, other: Result[B]) -> Result[B]:
        if not isinstance(other, Result):
            raise TypeError(f"Cannot use & with {type(other)} and Result")
        
        return self.and_then(lambda _: other)
        
    def void(self) -> Result[tuple[()]]:
        return self.map(lambda _: ())


class Success(Result[A]):
    def __init__(self, value: A, log: Optional[Log] = None):
        self.value = value
        self.log = log or Log()


class Err(Result[A]):
    def __init__(self, log: Log):
        self.log = log

def is_successful(result: Result[A]) -> TypeIs[Success[A]]:
    return isinstance(result, Success)

def is_err(result: Result[A]) -> TypeIs[Err[A]]:
    return isinstance(result, Err)