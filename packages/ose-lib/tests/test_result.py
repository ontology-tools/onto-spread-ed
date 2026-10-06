import pytest

from ose.result import (
    Err,
    Log,
    ResultContext,
    ResultFailedException,
    Success,
    is_err,
    is_successful,
)


def test_log_applies_template_to_messages():
    log = Log(template={"file": "a.xlsx"})
    log.error(type="e", row=1)
    log.warning(type="w")
    log.info(type="i", file="override.xlsx")

    assert log.errors == [{"file": "a.xlsx", "type": "e", "row": 1}]
    assert log.warnings == [{"file": "a.xlsx", "type": "w"}]
    assert log.infos == [{"file": "override.xlsx", "type": "i"}]
    assert log.has_errors()
    assert not Log().has_errors()


def test_log_merge_concatenates_and_does_not_mutate():
    a, b = Log(template={"x": 1}), Log(template={"y": 2})
    a.error(type="a")
    b.error(type="b")
    b.warning(type="w")

    merged = a + b

    assert [e["type"] for e in merged.errors] == ["a", "b"]
    assert [w["type"] for w in merged.warnings] == ["w"]
    assert merged.template == {"x": 1, "y": 2}
    assert len(a.errors) == 1 and len(b.errors) == 1


def test_log_plus_successful_result_merges_its_log():
    log = Log()
    other = Log()
    other.warning(type="w")

    log += Success((), other)

    assert log.warnings == [{"type": "w"}]


def test_log_plus_failed_result_raises():
    failed = Log()
    failed.error(type="boom")

    with pytest.raises(ResultFailedException) as e:
        _ = Log() + Err(failed)

    assert e.value.result.log is failed


def test_log_plus_other_type_raises_type_error():
    with pytest.raises(TypeError):
        _ = Log() + 1  # type: ignore[operator]


def test_to_result_depends_on_errors():
    ok = Log()
    ok.warning(type="w")
    assert is_successful(r := ok.to_result(42)) and r.value == 42
    assert r.log is ok

    bad = Log()
    bad.error(type="e")
    assert is_err(bad.to_result(42))
    assert is_err(Log().fail())


def test_success_and_err_properties():
    assert Success(1).successful and not Success(1).failed
    assert Err(Log()).failed and not Err(Log()).successful
    assert Success(1).log == Log()


def test_value_or_raise():
    assert Success("v").value_or_raise() == "v"
    with pytest.raises(ResultFailedException):
        Err(Log()).value_or_raise()


def test_map_and_void():
    assert Success(2).map(lambda x: x * 3).value == 6  # type: ignore[attr-defined]
    assert Success(2).void().value == ()  # type: ignore[attr-defined]

    err = Err(Log())
    assert err.map(lambda x: x * 3) is err


def test_and_then_combines_logs():
    first, second = Log(), Log()
    first.warning(type="first")
    second.warning(type="second")

    result = Success(1, first).and_then(lambda v: Success(v + 1, second))

    assert is_successful(result) and result.value == 2
    assert [w["type"] for w in result.log.warnings] == ["first", "second"]

    err = Err(Log())
    assert err.and_then(lambda v: Success(v)) is err


def test_and_operator_returns_second_on_success():
    second = Success("b")
    assert (Success("a") & second).value == "b"  # type: ignore[attr-defined]
    assert (Err(Log()) & second).failed

    with pytest.raises(TypeError):
        _ = Success("a") & "b"  # type: ignore[operator]


def test_result_context_turns_exception_into_error():
    with ResultContext() as log:
        raise RuntimeError("boom")

    assert log.has_errors()
    assert log.errors[0]["type"] == "exception"
    assert "boom" in str(log.errors[0])


def test_result_context_absorbs_failed_result_log():
    failed = Log()
    failed.error(type="inner")

    with ResultContext() as log:
        log += Err(failed)

    assert [e["type"] for e in log.errors] == ["inner"]


def test_result_context_uses_given_log():
    existing = Log()
    with ResultContext(existing) as log:
        log.warning(type="w")

    assert log is existing and existing.warnings == [{"type": "w"}]
