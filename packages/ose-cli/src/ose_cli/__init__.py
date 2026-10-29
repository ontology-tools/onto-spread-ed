"""Standalone command line interface for ose-lib."""

from importlib.metadata import PackageNotFoundError, version
from typing import Protocol

import click

try:
    __version__ = version("ose-cli")
except PackageNotFoundError:
    __version__ = "unknown"


class CLIHost(Protocol):
    @property
    def cli(self) -> click.Group: ...


def init_app(app: CLIHost, injector: object | None = None) -> None:
    """Register the standalone Click group with an optional Flask host."""
    from .main import cli

    app.cli.add_command(cli, name="ose")
