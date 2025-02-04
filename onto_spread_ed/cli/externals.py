import json
import logging
from typing import Callable, Any

import click
from flask.cli import AppGroup

from onto_spread_ed.commands.CLICommandContext import CLICommandContext
from onto_spread_ed.commands.ImportExternalCommand import ImportExternalCommand
from onto_spread_ed.model.ReleaseScript import ReleaseScript

logger = logging.getLogger(__name__)


def init_commands(cli: AppGroup, inject: Callable[[Any], Callable[[tuple[Any, ...], dict[str, Any]], Any]]):
    @cli.group("externals")
    def group():
        pass

    @group.command("build")
    @click.option("--release_script", "-r", default=".onto-ed/release_script.json")
    @click.option("--local_path", "-l", default=".")
    @click.option('-v', '--verbose', count=True)
    @inject
    def build(release_script: str, local_path: str, verbose: int):
        # set log level
        log_level = logging.WARN if verbose == 1 else (
            logging.INFO if verbose == 2 else (
                logging.DEBUG if verbose >= 3 else logging.ERROR))

        if not isinstance(log_level, int):
            raise ValueError('Invalid log level: %s' % log_level)
        logging.basicConfig(level=log_level)
        logging.root.setLevel(log_level)

        logger.debug(f"Loading release script from {release_script}")
        with open(release_script, "r") as f:
            data = json.load(f)
            script = ReleaseScript.from_json(data)

        context = CLICommandContext(local_path)
        command = ImportExternalCommand(context)

        command.run(script, local_path)

        pass
