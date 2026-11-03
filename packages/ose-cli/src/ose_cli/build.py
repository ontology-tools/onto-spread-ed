"""Build workspace preparation, persistence, execution and artifact publication."""

import asyncio
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, TypedDict, cast, get_args, get_origin

import click

from ose.building import available_stages, run_build
from ose.building.BuildContext import BuildContext, _BuildContextStageResult
from ose.building.Progress import Progress
from ose.building.stages import BuildStage
from ose.project import BuildConfiguration, BuildStep

from .common import Options, command_errors
from .diagnostics import Severity, format_state

STATE_FILE = ".ose-build.json"


class BuildMetadata(TypedDict):
    project_root: str
    temporary: bool
    keep: bool
    write: bool
    out: str | None
    robot_cache: str | None
    skipped: list[dict[str, str]]
    report_files: list[str] | None


def stage_context(cls: type[BuildStage[Any]]) -> type[BuildContext]:
    """Find a stage's context, including aliases such as ReleaseStage."""
    for base in cls.__mro__:
        for generic in base.__dict__.get("__orig_bases__", ()):
            origin = get_origin(generic)
            if origin and isinstance(origin, type) and issubclass(origin, BuildStage):
                for arg in get_args(generic):
                    if isinstance(arg, type) and issubclass(arg, BuildContext):
                        return arg
    return BuildContext


def output_options[F: Callable[..., Any]](fn: F) -> F:
    fn = click.option("--write", is_flag=True, help="Copy final artifacts into the original project.")(fn)
    return click.option(
        "--out", type=click.Path(file_okay=False, path_type=Path), help="Copy final artifacts below DIR."
    )(fn)


class BuildGroup(click.Group):
    """Allow both `build CONFIG` and `build resume/status BUILD_DIR`."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        if args and args[0] in self.commands:
            result = super().parse_args(ctx, ["", *args])
            ctx.params["config"] = None
            return result
        ctx.allow_interspersed_args = True
        return super().parse_args(ctx, args)


@click.group(cls=BuildGroup, invoke_without_command=True)
@click.argument("config", required=False)
@click.option("--stage", "stages", multiple=True, help="Run these stages in order instead of CONFIG.")
@click.option("--skip", multiple=True, help="Remove stages by name.")
@click.option("--build-dir", type=click.Path(file_okay=False, path_type=Path))
@click.option("--in-place", is_flag=True)
@output_options
@click.option("--keep", is_flag=True, help="Retain the temporary workspace after success.")
@click.option("--robot-cache", type=click.Path(file_okay=False, path_type=Path))
@click.pass_context
@command_errors
def build(
    ctx: click.Context,
    config: str | None,
    stages: tuple[str, ...],
    skip: tuple[str, ...],
    build_dir: Path | None,
    in_place: bool,
    out: Path | None,
    write: bool,
    keep: bool,
    robot_cache: Path | None,
) -> None:
    """Run CONFIG, or use --stage for an ad-hoc build.

    With no CONFIG, use 'default', or the sole build configuration.
    """
    if ctx.invoked_subcommand:
        if any((stages, skip, build_dir, in_place, out, write, keep, robot_cache)):
            raise click.UsageError("Build options belong to a new build; put resume options after 'resume'.")
        return
    start_build(
        ctx.obj,
        config=config,
        stages=stages,
        skip=skip,
        build_dir=build_dir,
        in_place=in_place,
        out=out,
        write=write,
        keep=keep,
        robot_cache=robot_cache,
    )


def contained_path(root: str | Path, relative: str) -> Path:
    root = Path(root).resolve()
    if Path(relative).is_absolute():
        raise click.ClickException(f"Expected a relative path below {root}: {relative}")
    path = (root / relative).resolve()
    if path == root or not path.is_relative_to(root):
        raise click.ClickException(f"Path escapes directory {root}: {relative}")
    return path


def save(context: BuildContext, metadata: BuildMetadata) -> None:
    path = Path(context.build_dir) / STATE_FILE
    data = context.model_dump(mode="json")
    data["cli"] = metadata
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2))
    temporary.replace(path)


def load(build_dir: Path) -> tuple[BuildContext, BuildMetadata]:
    build_dir = build_dir.resolve()
    data = json.loads((build_dir / STATE_FILE).read_text())
    metadata = data.pop("cli")
    if Path(data["build_dir"]).resolve() != build_dir:
        raise click.ClickException("Build directory has moved; restore it to the path recorded in .ose-build.json.")
    return BuildContext.model_validate(data), metadata


@contextmanager
def robot_environment(cache: str | None) -> Iterator[None]:
    old = os.environ.get("OSE_ROBOT_CACHE_DIR")
    if cache:
        os.environ["OSE_ROBOT_CACHE_DIR"] = str(Path(cache).resolve())
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("OSE_ROBOT_CACHE_DIR", None)
        else:
            os.environ["OSE_ROBOT_CACHE_DIR"] = old


@contextmanager
def result_logging() -> Iterator[None]:
    """The CLI presents runner errors through the structured stage result."""
    logger = logging.getLogger("ose.building.run")

    def handled_by_result(record: logging.LogRecord) -> bool:
        return record.levelno < logging.ERROR

    logger.addFilter(handled_by_result)
    try:
        yield
    finally:
        logger.removeFilter(handled_by_result)


def start_build(
    options: Options,
    *,
    config: str | None = None,
    stages: Sequence[str] = (),
    skip: Sequence[str] = (),
    build_dir: Path | None = None,
    in_place: bool = False,
    out: Path | None = None,
    write: bool = False,
    keep: bool = False,
    robot_cache: Path | None = None,
    stage_args: dict[str, Any] | None = None,
    report_files: Sequence[str] | None = None,
) -> None:
    if config and stages:
        raise click.UsageError("CONFIG and --stage are mutually exclusive")
    if in_place and build_dir:
        raise click.UsageError("--in-place and --build-dir are mutually exclusive")
    project = options.load_project()
    if stages:
        configuration = BuildConfiguration(
            name="ad-hoc", stages=[BuildStep(name=s, args=stage_args or {}) for s in stages]
        )
    else:
        if config is None:
            names = [c.name for c in project.build_configurations]
            if "default" in names:
                config = "default"
            elif len(names) == 1:
                config = names[0]
            else:
                raise click.UsageError("Choose CONFIG or --stage. Available configurations: " + ", ".join(names))
        configuration = project.build_configuration(config).model_copy(deep=True)
    registry = available_stages()
    configured_names = {s.name for s in configuration.stages}
    unknown = configured_names - set(skip) - set(registry)
    if unknown:
        raise click.UsageError("Unknown build stages: " + ", ".join(sorted(unknown)))
    unknown_skip = set(skip) - (set(registry) | configured_names)
    if unknown_skip:
        raise click.UsageError("Unknown stages to skip: " + ", ".join(sorted(unknown_skip)))
    selected = []
    skipped = []
    for step in configuration.stages:
        if step.name in skip:
            skipped.append(dict(name=step.name, reason="--skip"))
            continue
        required = stage_context(registry[step.name])
        if not issubclass(BuildContext, required):
            reason = f"requires {required.__module__}.{required.__name__}"
            options.warning(f"Skipping {step.name}: {reason}")
            skipped.append(dict(name=step.name, reason=reason))
        else:
            selected.append(step)
    configuration.stages = selected

    root = options.root.resolve()
    if not root.is_dir():
        raise click.ClickException(f"Project root is not a directory: {root}")
    # Reject inputs that would let stages modify files outside the workspace.
    for f in [project.external, *project.files.values()]:
        for path in [f.target.file, *(s.file for s in f.sources), f.renameTermFile, f.addParentsFile]:
            if path:
                contained_path(root, path)

    temporary = not in_place and build_dir is None
    if in_place:
        directory = root
    elif build_dir:
        directory = build_dir.resolve()
        if root == directory or root.is_relative_to(directory):
            raise click.UsageError("--build-dir must not be the project root or an ancestor; use --in-place.")
        if directory.exists() and any(directory.iterdir()):
            raise click.UsageError("--build-dir must be empty (use build resume for an existing build)")
    else:
        directory = Path(tempfile.mkdtemp(prefix=f"ose-build-{project.short_name}-"))

    if not in_place:

        def ignore(source: str, names: list[str]) -> list[str]:
            return [
                name
                for name in names
                if name in {".git", STATE_FILE, STATE_FILE + ".tmp"} or (Path(source) / name).resolve() == directory
            ]

        shutil.copytree(root, directory, dirs_exist_ok=True, ignore=ignore)
    elif (directory / STATE_FILE).exists():
        previous, _ = load(directory)
        if previous.state != "completed":
            raise click.UsageError("An unfinished in-place build exists; resume it or move .ose-build.json first.")

    context = BuildContext(project=project, build_configuration=configuration, build_dir=str(directory))
    metadata: BuildMetadata = dict(
        project_root=str(root),
        temporary=temporary,
        keep=keep,
        write=write or in_place,
        out=str(out.resolve()) if out else None,
        robot_cache=str(robot_cache.resolve()) if robot_cache else None,
        skipped=skipped,
        report_files=list(report_files) if report_files is not None else None,
    )
    execute(options, context, metadata)


def status_data(context: BuildContext, metadata: BuildMetadata) -> dict[str, Any]:
    serialized_results = context.model_dump(mode="json")["stage_results"]
    data: dict[str, Any] = dict(
        state=context.state,
        build_dir=context.build_dir,
        configuration=context.build_configuration.name,
        stages=[],
        artifacts=[a.model_dump(mode="json") for a in context.artifacts],
        skipped=metadata.get("skipped", []),
    )
    for step, result, serialized in zip(context.build_configuration.stages, context.stage_results, serialized_results):
        data["stages"].append(
            dict(
                name=step.name,
                result=result.result if result else "pending",
                errors=len(result.log.errors) if result else 0,
                warnings=len(result.log.warnings) if result else 0,
                data=serialized["data"] if serialized else {},
                log=serialized["log"] if serialized else None,
            )
        )
    return data


def publish(context: BuildContext, destinations: Iterable[Path]) -> None:
    copies = []
    for destination in destinations:
        for artifact in context.final_artifacts():
            source = contained_path(context.build_dir, artifact.local_path)
            target = contained_path(destination, cast(str, artifact.final_path))
            if not source.is_file():
                raise click.ClickException(f"Final artifact is missing: {source}")
            copies.append((source, target))
    for source, target in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        if source != target:
            shutil.copy2(source, target)


def execute(options: Options, context: BuildContext, metadata: BuildMetadata) -> None:
    save(context, metadata)
    options.notice(f"Build directory: {context.build_dir}")

    def done(c: BuildContext, stage: BuildStage[BuildContext], result: _BuildContextStageResult) -> None:
        save(c, metadata)
        severity: Severity = (
            "error"
            if result.result in {"failed", "cancelled"}
            else ("warning" if result.result in {"paused", "skipped"} or result.log.warnings else "info")
        )
        options.message(
            severity,
            f"{stage.name()}: {format_state(result.result)} "
            f"({len(result.log.errors)} errors, {len(result.log.warnings)} warnings)",
        )
        options.log(result.log)

    def progress(c: BuildContext, p: Progress) -> None:
        save(c, metadata)
        if options.verbose:
            options.notice(f"{p.message or ''} {p.item or ''}".strip())

    try:
        with robot_environment(metadata.get("robot_cache")), result_logging():
            asyncio.run(run_build(context, on_progress=progress, on_stage_done=done))
        save(context, metadata)
        if context.state == "completed":
            destinations = [
                Path(p) for p in [metadata.get("out"), metadata["project_root"] if metadata.get("write") else None] if p
            ]
            publish(context, destinations)
    except BaseException:
        # Keep a resumable snapshot even when a stage constructor or publishing fails.
        save(context, metadata)
        raise

    data = status_data(context, metadata)
    lines = [f"Build {format_state(context.state)}"]
    if metadata.get("report_files") is not None:
        report: dict[str, Any] = next((s["data"] for s in data["stages"] if s["name"] == "VALIDATION"), {})
        keys = metadata["report_files"]
        data["report"] = {k: v for k, v in report.items() if not keys or k in keys}
        lines += [
            f"{k}: {format_state('skipped' if v.get('skipped') else 'valid' if v['valid'] else 'invalid')} "
            f"({len(v['errors'])} errors, {len(v['warnings'])} warnings)"
            for k, v in data["report"].items()
        ]
    options.emit(data, lines)
    if context.state == "completed" and metadata["temporary"] and not metadata["keep"]:
        shutil.rmtree(context.build_dir)
    if context.state != "completed":
        raise click.exceptions.Exit(1)


@build.command("resume")
@click.argument("build_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--skip-current", is_flag=True)
@output_options
@click.pass_obj
@command_errors
def resume(options: Options, build_dir: Path, skip_current: bool, out: Path | None, write: bool) -> None:
    """Continue a saved build; failed stages are retried unless skipped."""
    context, metadata = load(build_dir)
    if skip_current:
        context.skip_current_stage()
    if out:
        metadata["out"] = str(out.resolve())
    if write:
        metadata["write"] = True
    execute(options, context, metadata)


@build.command("status")
@click.argument("build_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.pass_obj
@command_errors
def status(options: Options, build_dir: Path) -> None:
    """Display saved build state, stage diagnostics and artifacts."""
    context, metadata = load(build_dir)
    data = status_data(context, metadata)
    lines = [f"Build {format_state(data['state'])}: {data['build_dir']}"]
    lines += [
        f"{s['name']}: {format_state(s['result'])} ({s['errors']} errors, {s['warnings']} warnings)"
        for s in data["stages"]
    ]
    lines += [f"{a['kind']}: {a['local_path']} → {a['final_path'] or '-'}" for a in data["artifacts"]]
    options.emit(data, lines)
    for result in context.stage_results:
        if result is not None:
            options.log(result.log)
