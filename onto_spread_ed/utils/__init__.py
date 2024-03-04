import typing

from .github import *  # noqa: F403, F401


def str_empty(value: typing.Optional[str]) -> bool:
    return value is None or not any(value.strip())


def lower(string: typing.Optional[str]) -> typing.Optional[str]:
    return string.lower() if string is not None else None
