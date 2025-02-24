from typing import Callable, Any

import click
from flask.cli import AppGroup
from flask_sqlalchemy import SQLAlchemy

from ose.release.BuildReleaseStep import BuildReleaseStep
from ose.release.ImportExternalReleaseStep import ImportExternalReleaseStep


def init_commands(cli: AppGroup, inject: Callable[[Any], Callable[[tuple[Any, ...], dict[str, Any]], Any]]):
    @cli.group("release")
    def group():
        pass
