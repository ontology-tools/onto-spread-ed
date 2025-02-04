from typing import Callable, Any

import click
from flask.cli import AppGroup
from flask_sqlalchemy import SQLAlchemy

from onto_spread_ed.release.BuildReleaseStep import BuildReleaseStep
from onto_spread_ed.release.ImportExternalReleaseStep import ImportExternalReleaseStep


def init_commands(cli: AppGroup, inject: Callable[[Any], Callable[[tuple[Any, ...], dict[str, Any]], Any]]):
    @cli.group("release")
    def group():
        pass

    @group.command("build-external")
    @click.option("--release_script", "-r", default=".onto-ed/release_script.json")
    @click.option("--local_path", "-l", default=".")
    @inject
    def build(release_script: str, local_path: str, db: SQLAlchemy):
        print(f"Building release script {release_script} at {local_path}")

        step = BuildReleaseStep(db, None, )

        pass
