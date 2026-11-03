from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Concatenate,
    Coroutine,
    Never,
    Optional,
    TypeIs,
    cast,
    overload,
)

Message = dict[str, Any]


@dataclass
class Log:
    template: Message = field(default_factory=dict)
    errors: list[Message] = field(default_factory=list)
    warnings: list[Message] = field(default_factory=list)
    infos: list[Message] = field(default_factory=list)
    debugs: list[Message] = field(default_factory=list)

    def error(self, type: str, **kwargs) -> None:
        self.errors.append({**self.template, **kwargs, "type": type})

    def warning(self, type: str, **kwargs) -> None:
        self.warnings.append({**self.template, **kwargs, "type": type})

    def info(self, type: str, **kwargs) -> None:
        self.infos.append({**self.template, **kwargs, "type": type})

    def debug(self, type: str, **kwargs) -> None:
        self.debugs.append({**self.template, **kwargs, "type": type})

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def merge(self, other: Log) -> Log:
        return Log(
            template=dict(self.template),
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
            infos=self.infos + other.infos,
            debugs=self.debugs + other.debugs,
        )


class Result[A]:
    log: Log

    @property
    def successful(self) -> bool:
        return isinstance(self, Success)

    @property
    def failed(self) -> bool:
        return isinstance(self, Err)

    def value_or_raise(self) -> A:
        if isinstance(self, Success):
            return self.value

        raise ValueError(f"Cannot get value of failed result: {self.log}")

    def map[B](self, func: Callable[[A], B]) -> Result[B]:
        if isinstance(self, Success):
            return Success(func(self.value), self.log)
        else:
            return cast(Result[B], self)

    def and_then[B](self, func: Callable[[A], Result[B]]) -> Result[B]:
        if isinstance(self, Success):
            new = func(self.value)
            log = self.log.merge(new.log)
            return Success(new.value, log) if isinstance(new, Success) else Err(log)
        else:
            return cast(Result[B], self)

    def void(self) -> Result[tuple[()]]:
        return self.map(lambda _: ())


class Success[A](Result[A]):
    def __init__(self, value: A, log: Optional[Log] = None):
        log = log if log is not None else Log()
        if log.has_errors():
            raise ValueError(f"A successful result cannot have errors: {log.errors}")

        self.value = value
        self.log = log


class Err[A](Result[A]):
    def __init__(self, log: Log):
        self.log = log


def is_successful[A](result: Result[A]) -> TypeIs[Success[A]]:
    return isinstance(result, Success)


def is_err[A](result: Result[A]) -> TypeIs[Err[A]]:
    return isinstance(result, Err)


class _Abort(BaseException):
    """Ends a result context early. A BaseException, so `except Exception` inside it doesn't swallow it."""


class ResultContext:
    def __init__(self) -> None:
        self.log = Log()

    def unwrap[A](self, result: Result[A]) -> A:
        self.log = self.log.merge(result.log)
        if isinstance(result, Success):
            return result.value

        raise _Abort()

    def attempt[A](self, result: Result[A]) -> A | None:
        """Attempt to unwrap a result. Continues even if the result failed. If it has errors, the result will be failed in the end."""
        self.log = self.log.merge(result.log)
        return result.value if isinstance(result, Success) else None

    def fail(self, **error: Any) -> Never:
        """Ends the context as failed, adding `error` if given."""
        if error:
            self.log.error(**error)

        raise _Abort()


def _to_result[A](value: A, log: Log) -> Result[A]:
    return Err(log) if log.has_errors() else Success(value, log)


def _wrap(fn: Callable[..., Any], position: int) -> Callable[..., Any]:
    """Runs `fn` in a fresh `ResultContext`, passed as positional argument `position`."""
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_block(*args, **kwargs):
            ctx = ResultContext()
            try:
                value = await fn(*args[:position], ctx, *args[position:], **kwargs)
            except _Abort:
                return Err(ctx.log)
            return _to_result(value, ctx.log)

        return async_block

    @functools.wraps(fn)
    def block(*args, **kwargs):
        ctx = ResultContext()
        try:
            value = fn(*args[:position], ctx, *args[position:], **kwargs)
        except _Abort:
            return Err(ctx.log)
        return _to_result(value, ctx.log)

    return block


@overload
def with_result_context[**P, A](  # type: ignore[overload-overlap]
    fn: Callable[Concatenate[ResultContext, P], Coroutine[Any, Any, A]],
) -> Callable[P, Coroutine[Any, Any, Result[A]]]: ...
@overload
def with_result_context[**P, A](fn: Callable[Concatenate[ResultContext, P], A]) -> Callable[P, Result[A]]: ...
def with_result_context(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Turns `fn(ctx: ResultContext, ...) -> A` into `fn(...) -> Result[A]`"""
    return _wrap(fn, 0)


@overload
def with_result_context_method[S, **P, A](  # type: ignore[overload-overlap]
    fn: Callable[Concatenate[S, ResultContext, P], Coroutine[Any, Any, A]],
) -> Callable[Concatenate[S, P], Coroutine[Any, Any, Result[A]]]: ...
@overload
def with_result_context_method[S, **P, A](
    fn: Callable[Concatenate[S, ResultContext, P], A],
) -> Callable[Concatenate[S, P], Result[A]]: ...
def with_result_context_method(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Turns the method `fn(self, ctx: ResultContext, ...) -> A` into `fn(self, ...) -> Result[A]`"""
    return _wrap(fn, 1)
