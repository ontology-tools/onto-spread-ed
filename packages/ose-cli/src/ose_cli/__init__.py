"""
OSE CLI - Command Line Interface for OntoSpreadEd

This package provides CLI commands for the OntoSpreadEd
ontology spreadsheet editor.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-cli")
except PackageNotFoundError:
    __version__ = "unknown"

from flask import Flask
from flask.cli import AppGroup


def init_app(app: Flask):
    ose_group = AppGroup("ose", help="Commands for OntoSpreadEd")

    from .release import register_commands as release
    from .externals import register_commands as externals

    release(ose_group)
    externals(ose_group)

    app.cli.add_command(ose_group)
