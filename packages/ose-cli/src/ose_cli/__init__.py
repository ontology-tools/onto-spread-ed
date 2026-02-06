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

import functools

from flask import Flask
from flask.cli import AppGroup
from injector import Injector, inject


def init_app(app: Flask, injector: Injector):
    ose_group = AppGroup("ose", help="Commands for OntoSpreadEd")

    cli_groups = []

    from .release import init_commands as release

    cli_groups.append(release)

    from .externals import init_commands as externals

    cli_groups.append(externals)

    def with_injector(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return injector.call_with_injection(callable=inject(fn), args=args, kwargs=kwargs)

        return wrapper

    for init_group in cli_groups:
        init_group(ose_group, with_injector)

    app.cli.add_command(ose_group)
