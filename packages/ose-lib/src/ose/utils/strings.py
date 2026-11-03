import re
import typing


def str_empty(value: typing.Optional[str]) -> bool:
    return value is None or not any(value.strip())


def str_space_eq(a: typing.Optional[str], b: typing.Optional[str], none_as_empty=True) -> bool:
    """
    Checks if two strings are equivalent ignoring differences in spaces (leading, trailing, and difference in
    repetitions)

    @param a: First string
    @param b: Second string
    @param none_as_empty: Whether `None` should be treated as empty string
    @return:
    """
    if a is None and b is None:
        return True

    if a is None and none_as_empty:
        a = ""

    if b is None and none_as_empty:
        b = ""

    if a is None or b is None:
        return False

    a = re.sub(r"\s{2,}", " ", a)
    b = re.sub(r"\s{2,}", " ", b)

    return a.strip() == b.strip()


def lower(string: typing.Optional[str]) -> typing.Optional[str]:
    return string.lower() if string is not None else None


def letters(string: typing.Optional[str]) -> typing.Optional[str]:
    return string.strip().replace(" ", "").replace("-", "").lower() if string is not None else None
