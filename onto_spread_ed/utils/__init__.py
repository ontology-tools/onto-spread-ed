import typing

from .github import *


def str_empty(value: typing.Optional[str]) -> bool:
    return value is None or not any(value.strip())
