from typing import Callable, Any

from flask.cli import AppGroup


def init_commands(cli: AppGroup, _: Callable[[Any], Callable[[tuple[Any, ...], dict[str, Any]], Any]]):
    @cli.group("release")
    def group():
        pass
