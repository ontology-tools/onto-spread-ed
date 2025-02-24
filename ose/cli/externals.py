import json
import logging
import shutil
from typing import Callable, Any, Dict, Tuple

import click
from flask.cli import AppGroup

from ..commands.CLICommandContext import CLICommandContext
from ..commands.ImportExternalCommand import ImportExternalCommand
from ..model.ReleaseScript import ReleaseScript

logger = logging.getLogger(__name__)


def init_commands(cli: AppGroup, inject: Callable[[Any], Callable[[Tuple[Any, ...], Dict[str, Any]], Any]]):
    @cli.group("externals")
    def group():
        pass

    @group.command("build")
    @click.option("--out", "-o", default="externals.owl")
    @click.option("--release-script", "-r", default=".onto-ed/release_script.json")
    @click.option("--local-path", "-l", default=".")
    @click.option('-v', '--verbose', count=True, default=2)
    @inject
    def build(release_script: str, local_path: str, verbose: int, out: str):
        # set log level
        log_level = logging.WARN if verbose == 1 else (
            logging.INFO if verbose == 2 else (
                logging.DEBUG if verbose >= 3 else logging.ERROR))

        if not isinstance(log_level, int):
            raise ValueError('Invalid log level: %s' % log_level)
        logging.basicConfig(level=log_level)
        logging.root.setLevel(log_level)

        logger.info(f"Loading release script from {release_script}")
        with open(release_script, "r") as f:
            data = json.load(f)
            script = ReleaseScript.from_json(data)

        context = CLICommandContext(local_path)
        command = ImportExternalCommand(context)

        logger.info("Running external build command")
        command.run(script, local_path)

        outfile = context.local_name(script.external.target.file)
        shutil.copy(outfile, out)
        logger.info(f"External file written to {outfile}")
