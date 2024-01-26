import typing

from .github import *  # noqa: F403, F401


def str_empty(value: typing.Optional[str]) -> bool:
    return value is None or not any(value.strip())
