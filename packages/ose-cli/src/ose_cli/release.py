"""
CLI commands for running ontology releases locally.

This module provides CLI commands for running release steps on local ontology directories
using the core ReleaseStep classes with a CLIReleaseContext, without requiring the Flask
application or database.
"""
import json
import logging
import os
from typing import Optional

import click
import yaml
from dacite import from_dict

from ose.model.ReleaseScript import ReleaseScript
from ose.model.RepositoryConfiguration import RepositoryConfiguration
from ose.release.CLIReleaseContext import CLIReleaseContext
from ose.release.do_release import BUILT_IN_RELEASE_STEPS_DICT
from ose.release.ReleaseStep import ReleaseStep
from ose.services.PluginService import discover_plugins

logger = logging.getLogger(__name__)


def _build_step_registry() -> dict:
    """Build the combined registry of built-in + plugin release steps."""
    registry = BUILT_IN_RELEASE_STEPS_DICT.copy()
    for plugin, _ in discover_plugins():
        for content_type in plugin.contents:
            if isinstance(content_type, type) and issubclass(content_type, ReleaseStep):
                registry[content_type.name()] = content_type
    return registry


def load_repo_config(local_path: str) -> RepositoryConfiguration:
    """Load RepositoryConfiguration from <local_path>/.onto-ed/config.yaml."""
    config_path = os.path.join(local_path, ".onto-ed", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Repository configuration not found: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return from_dict(RepositoryConfiguration, data)


def register_commands(cli):
    """Register release commands to the CLI (standalone Click)"""
    @cli.group("release")
    def release_group():
        """Commands for managing releases"""
        pass

    @release_group.command("run")
    @click.option("--release-script", "-r", default=".onto-ed/release_script.json",
                  help="Path to release script JSON file")
    @click.option("--local-path", "-l", default=".",
                  help="Local working directory (ontology repository root)")
    @click.option("--steps", "-s", default=None,
                  help="Comma-separated list of steps to run (e.g., PREPARATION,IMPORT_EXTERNAL,VALIDATION,BUILD,MERGE)")
    @click.option('-v', '--verbose', count=True, default=2,
                  help="Verbosity level (use multiple times for more verbose)")
    def run(release_script: str, local_path: str, steps: Optional[str], verbose: int):
        """Run release steps on a local ontology directory.

        This command runs specified release steps locally without requiring
        the Flask application or database. Steps are executed in order.

        If --steps is not specified, runs all steps defined in the release script.
        """
        # Set log level
        log_level = logging.WARN if verbose == 1 else (
            logging.INFO if verbose == 2 else (
                logging.DEBUG if verbose >= 3 else logging.ERROR))

        logging.basicConfig(level=log_level, format='%(levelname)s - %(name)s - %(message)s')
        logging.root.setLevel(log_level)

        logger.info(f"Loading release script from {release_script}")

        try:
            with open(release_script, "r") as f:
                data = json.load(f)
                script = ReleaseScript.from_json(data)
        except FileNotFoundError:
            logger.error(f"Release script not found: {release_script}")
            raise SystemExit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in release script: {e}")
            raise SystemExit(1)

        local_path = os.path.abspath(local_path)

        # Load repository configuration
        try:
            repo_config = load_repo_config(local_path)
        except FileNotFoundError as e:
            logger.error(str(e))
            raise SystemExit(1)
        except Exception as e:
            logger.error(f"Failed to load repository configuration: {e}")
            raise SystemExit(1)

        # Build step registry
        available_steps = _build_step_registry()

        # Determine steps to run
        if steps:
            step_names = [s.strip().upper() for s in steps.split(",")]
        else:
            # Use all steps from the release script
            step_names = [s.name for s in script.steps]

        # Validate step names
        for step_name in step_names:
            if step_name not in available_steps:
                logger.error(f"Unknown release step: {step_name}")
                logger.error(f"Available steps: {', '.join(sorted(available_steps.keys()))}")
                raise SystemExit(1)

        # Get step arguments from release script
        step_args = {}
        for step in script.steps:
            step_args[step.name] = step.args

        logger.info(f"Running steps: {', '.join(step_names)}")

        # Create context with working_dir == repository_dir (files already in place)
        context = CLIReleaseContext(
            release_script=script,
            repo_config=repo_config,
            repository_dir=local_path,
            working_dir=local_path,
        )

        try:
            # Instantiate steps, skipping those that don't accept this context
            release_steps = []
            for step_name in step_names:
                step_class = available_steps[step_name]
                if not step_class.accepts_context(context):
                    logger.warning(f"Skipping step {step_name} (not compatible with this context)")
                    continue
                args = step_args.get(step_name, {})
                release_steps.append((step_name, step_class(context, **args)))

            # Run steps in sequence
            for step_name, step in release_steps:
                logger.info(f"\n{'='*60}\nRunning step: {step_name}\n{'='*60}")

                should_continue = step.run()
                if not should_continue:
                    logger.info(f"Step {step_name} signaled stop.")
                    break
            else:
                logger.info(f"\n{'='*60}\nRelease completed successfully!\n{'='*60}")
        finally:
            context.cleanup()

    @release_group.command("list-steps")
    def list_steps():
        """List available release steps."""
        available_steps = _build_step_registry()
        click.echo("Available release steps:")
        click.echo("")
        click.echo("  Built-in:")
        for name in BUILT_IN_RELEASE_STEPS_DICT:
            step_class = BUILT_IN_RELEASE_STEPS_DICT[name]
            doc = step_class.__doc__ or "No description"
            click.echo(f"    {name:25} {doc.strip().split(chr(10))[0]}")

        plugin_steps = {k: v for k, v in available_steps.items() if k not in BUILT_IN_RELEASE_STEPS_DICT}
        if plugin_steps:
            click.echo("")
            click.echo("  Plugins:")
            for name, step_class in plugin_steps.items():
                doc = step_class.__doc__ or "No description"
                click.echo(f"    {name:25} {doc.strip().split(chr(10))[0]}")


