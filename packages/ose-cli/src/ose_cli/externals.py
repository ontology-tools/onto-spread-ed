import json
import logging
import os
import shutil
from typing import Optional

import click

from ose.model.ReleaseScript import ReleaseScript
from ose.release.CLIReleaseContext import CLIReleaseContext
from ose.release.ImportExternalReleaseStep import ImportExternalReleaseStep

from .release import load_repo_config

logger = logging.getLogger(__name__)


def register_commands(cli):
    """Register externals commands to the CLI."""
    @cli.group("externals")
    def externals_group():
        """Commands for working with external ontologies"""
        pass

    @externals_group.command("build")
    @click.option("--out", "-o", default=None, help="Output file path")
    @click.option("--release-script", "-r", default=".onto-ed/release_script.json", help="Path to release script")
    @click.option("--local-path", "-l", default=".", help="Local working directory")
    @click.option('-v', '--verbose', count=True, default=2, help="Verbosity level (use multiple times for more verbose)")
    def build(release_script: str, local_path: str, verbose: int, out: Optional[str]):
        """Build external ontology files"""
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

        local_path = os.path.abspath(local_path)
        repo_config = load_repo_config(local_path)

        with CLIReleaseContext(
            release_script=script,
            repo_config=repo_config,
            repository_dir=local_path,
            working_dir=local_path,
        ) as context:
            step = ImportExternalReleaseStep(context, use_existing_file=False)

            logger.info("Running external build command")
            ok = step.run()

            result = context.result
            if result is not None:
                for error in result.errors:
                    logger.error(f"  {error}")
                for warning in result.warnings:
                    logger.warning(f"  {warning}")

            if not ok:
                logger.error("Command failed. Check the logs above!")
                raise SystemExit(1)

            outfile = context.local_name(script.external.target.file)

            if out is None:
                out = os.path.join(local_path, script.external.target.file)

            out = os.path.abspath(out)
            outfile = os.path.abspath(outfile)

            if out != outfile:
                shutil.copy(outfile, out)

            logger.info(f"External file written to {outfile}")
