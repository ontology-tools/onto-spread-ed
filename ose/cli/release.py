from typing import Callable, Any, Dict, Tuple

from flask.cli import AppGroup


def init_commands(cli: AppGroup, _: Callable[[Any], Callable[[Tuple[Any, ...], Dict[str, Any]], Any]]):
    @cli.group("release")
    def group():
        pass
