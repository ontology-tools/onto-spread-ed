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
