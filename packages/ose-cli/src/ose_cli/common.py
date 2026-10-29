"""Shared CLI options and error presentation."""

from collections.abc import Callable, Iterable
import functools
import json
from pathlib import Path

import click
import yaml

from ose.project import Project
from ose.result import Log, Message

from .diagnostics import COLORS, Severity, format_diagnostic


class Options:
    def __init__(
        self, project: str | Path, root: str | Path | None, verbose: int, quiet: bool, json_output: bool
    ) -> None:
        path = Path(project).resolve()
        if path.is_dir():
            path = path / ".onto-ed" / "config.yaml"
        self.config_path = path
        self.root = (
            Path(root).resolve() if root else (path.parent.parent if path.parent.name == ".onto-ed" else path.parent)
        )
        self.verbose = verbose
        self.quiet = quiet
        self.json = json_output

    def load_project(self) -> Project:
        try:
            return Project.model_validate(yaml.safe_load(self.config_path.read_text()))
        except (OSError, ValueError, yaml.YAMLError) as e:
            raise click.ClickException(f"Cannot load project {self.config_path}: {e}") from e

    def emit(self, data: object, lines: Iterable[str] = ()) -> None:
        if self.json:
            click.echo(json.dumps(data, indent=2, default=str))
        elif not self.quiet:
            for line in lines:
                click.echo(line)

    def notice(self, message: str) -> None:
        self.info(message)

    def message(self, severity: Severity, message: str) -> None:
        if self.quiet and severity != "error":
            return
        if severity == "debug" and not self.verbose:
            return
        prefix = click.style(severity.upper(), fg=COLORS[severity], bold=True)
        click.echo(f"{prefix}: {message}", err=True)

    def error(self, message: str) -> None:
        self.message("error", message)

    def warning(self, message: str) -> None:
        self.message("warning", message)

    def info(self, message: str) -> None:
        self.message("info", message)

    def log(self, log: Log) -> None:
        if self.json:
            return
        groups: tuple[tuple[Severity, list[Message]], ...] = (
            ("error", log.errors),
            ("warning", log.warnings),
            ("info", log.infos),
            ("debug", log.debugs),
        )
        for severity, diagnostics in groups:
            for diagnostic in diagnostics:
                self.message(severity, format_diagnostic(diagnostic, verbose=bool(self.verbose)))


def command_errors[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(fn)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(*args, **kwargs)
        except (OSError, ValueError, KeyError, yaml.YAMLError) as e:
            raise click.ClickException(str(e)) from e

    return wrapped
