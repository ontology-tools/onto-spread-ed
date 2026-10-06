import asyncio

import pytest

from ose.result import (
    ResultContext,
    Err,
    Log,
    Success,
    with_result_context,
    with_result_context_method,
    is_err,
    is_successful,
)


def failed(type: str = "inner") -> Err:
    log = Log()
    log.error(type=type)
    return Err(log)


def warned(value, type: str = "w") -> Success:
    log = Log()
    log.warning(type=type)
    return Success(value, log)


# --- Log ------------------------------------------------------------------------


def test_log_applies_template_to_messages():
    log = Log(template={"file": "a.xlsx"})
    log.error(type="e", row=1)
    log.warning(type="w")
    log.info(type="i", file="override.xlsx")
    log.debug(type="d")

    assert log.errors == [{"file": "a.xlsx", "type": "e", "row": 1}]
    assert log.warnings == [{"file": "a.xlsx", "type": "w"}]
    assert log.infos == [{"file": "override.xlsx", "type": "i"}]
    assert log.debugs == [{"file": "a.xlsx", "type": "d"}]
    assert log.has_errors()
    assert not Log().has_errors()


def test_log_merge_is_immutable_and_keeps_own_template():
    a, b = Log(template={"x": 1}), Log(template={"y": 2})
    a.error(type="a")
    b.error(type="b")
    b.debug(type="d")

    merged = a.merge(b)
    merged.warning(type="w")

    assert [e["type"] for e in merged.errors] == ["a", "b"]
    assert merged.debugs == [{"y": 2, "type": "d"}]
    assert merged.warnings == [{"x": 1, "type": "w"}]  # b's template doesn't leak into later messages
    assert len(a.errors) == 1 and a.warnings == [] and len(b.errors) == 1


# --- Result ---------------------------------------------------------------------


def test_success_cannot_have_errors():
    with pytest.raises(ValueError):
        Success(1, failed().log)


def test_err_may_have_no_errors():
    assert Err(Log()).failed


def test_success_and_err_properties():
    assert Success(1).successful and not Success(1).failed
    assert Err(Log()).failed and not Err(Log()).successful
    assert Success(1).log == Log()
    assert is_successful(Success(1)) and is_err(Err(Log()))


def test_value_or_raise():
    assert Success("v").value_or_raise() == "v"
    with pytest.raises(ValueError):
        failed().value_or_raise()


def test_map_and_void():
    assert Success(2).map(lambda x: x * 3).value == 6  # type: ignore[attr-defined]
    assert Success(2).void().value == ()  # type: ignore[attr-defined]

    err = Err(Log())
    assert err.map(lambda x: x * 3) is err


def test_and_then_combines_logs_without_mutating():
    first, second = warned(1, "first"), warned(None, "second")

    result = first.and_then(lambda v: Success(v + 1, second.log))

    assert is_successful(result) and result.value == 2
    assert [w["type"] for w in result.log.warnings] == ["first", "second"]
    assert len(first.log.warnings) == 1 and len(second.log.warnings) == 1

    combined_err = first.and_then(lambda _: failed())
    assert is_err(combined_err) and [w["type"] for w in combined_err.log.warnings] == ["first"]

    err = Err(Log())
    assert err.and_then(lambda v: Success(v)) is err


# --- ResultContext ------------------------------------------------------------


def test_context_returns_value_with_collected_log():
    @with_result_context
    def block(ctx: ResultContext, x: int) -> int:
        ctx.log.info(type="start")
        return ctx.unwrap(warned(x)) + 1

    result = block(1)

    assert is_successful(result) and result.value == 2
    assert [i["type"] for i in result.log.infos] == ["start"]
    assert [w["type"] for w in result.log.warnings] == ["w"]


def test_unwrap_ends_context_on_failure():
    reached = []

    @with_result_context
    def block(ctx: ResultContext) -> int:
        ctx.unwrap(failed())
        reached.append(True)
        return 1

    result = block()

    assert is_err(result) and [e["type"] for e in result.log.errors] == ["inner"]
    assert reached == []


def test_attempt_continues_and_fails_in_the_end():
    @with_result_context
    def block(ctx: ResultContext) -> list:
        return [ctx.attempt(failed("a")), ctx.attempt(Success(1)), ctx.attempt(failed("b"))]

    result = block()

    assert is_err(result) and [e["type"] for e in result.log.errors] == ["a", "b"]


def test_logged_error_fails_context():
    @with_result_context
    def block(ctx: ResultContext) -> int:
        ctx.log.error(type="bad")
        return 1

    assert is_err(block())


def test_fail_with_and_without_error():
    @with_result_context
    def with_error(ctx: ResultContext) -> int:
        ctx.fail(type="bad", msg="reason")

    @with_result_context
    def without_error(ctx: ResultContext) -> int:
        ctx.log.warning(type="skipped")
        ctx.fail()

    assert with_error().log.errors == [{"type": "bad", "msg": "reason"}]
    result = without_error()
    assert is_err(result) and result.log.errors == [] and result.log.warnings == [{"type": "skipped"}]


def test_fail_is_not_caught_by_broad_except():
    @with_result_context
    def block(ctx: ResultContext) -> int:
        try:
            ctx.fail(type="bad")
        except Exception:
            return 1

    assert is_err(block())


def test_exceptions_propagate():
    @with_result_context
    def block(ctx: ResultContext) -> int:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        block()


def test_cancellation_propagates():
    @with_result_context
    async def block(ctx: ResultContext) -> int:
        await asyncio.sleep(10)
        return 1

    async def main():
        task = asyncio.create_task(block())
        await asyncio.sleep(0)
        task.cancel()
        await task

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(main())


def test_nested_contexts_keep_their_own_log():
    @with_result_context
    def inner(ctx: ResultContext) -> int:
        ctx.log.warning(type="inner")
        ctx.fail(type="inner-error")

    @with_result_context
    def outer(ctx: ResultContext) -> int:
        ctx.log.template = {"file": "outer"}
        ctx.attempt(inner())
        ctx.log.warning(type="outer")
        return 1

    result = outer()

    assert result.log.warnings == [{"type": "inner"}, {"file": "outer", "type": "outer"}]
    assert result.log.errors == [{"type": "inner-error"}]


class Service:
    def __init__(self, offset: int):
        self.offset = offset

    @with_result_context_method
    def add(self, ctx: ResultContext, x: int) -> int:
        return ctx.unwrap(Success(x)) + self.offset

    @with_result_context_method
    async def add_async(self, ctx: ResultContext, x: int) -> int:
        await asyncio.sleep(0)
        return ctx.unwrap(Success(x)) + self.offset

    @classmethod
    @with_result_context_method
    def create(cls, ctx: ResultContext, offset: int) -> "Service":
        if offset < 0:
            ctx.fail(type="negative")
        return cls(offset)


def test_with_result_context_method_variants():
    service = Service(10)

    assert service.add(1).value == 11  # type: ignore[attr-defined]
    assert asyncio.run(service.add_async(2)).value == 12  # type: ignore[attr-defined]
    assert Service.create(3).value.offset == 3  # type: ignore[attr-defined]
    assert is_err(Service.create(-1))


def test_async_with_result_context():
    @with_result_context
    async def block(ctx: ResultContext, x: int) -> int:
        await asyncio.sleep(0)
        return ctx.unwrap(warned(x))

    result = asyncio.run(block(5))

    assert is_successful(result) and result.value == 5 and len(result.log.warnings) == 1
