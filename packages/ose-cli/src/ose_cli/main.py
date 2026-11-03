"""Project inspection and ontology builds without the web application."""

import graphlib
import logging
from pathlib import Path
from typing import get_args

import click

from ose.building import available_stages
from ose.building.BuildContext import BuildContext
from ose.ontology import DIAGNOSTIC_KIND
from ose.schema.Schema import BUILTIN_SCHEMAS, resolve_schema

from . import __version__
from .common import Options, command_errors
from .build import build, output_options, stage_context, start_build


@click.group()
@click.option("--project", "-p", default=".onto-ed/config.yaml", type=click.Path(path_type=Path), show_default=True)
@click.option(
    "--root",
    type=click.Path(file_okay=False, path_type=Path),
    help="Project tree (defaults to config's project directory).",
)
@click.option("--verbose", "-v", count=True)
@click.option("--quiet", "-q", is_flag=True)
@click.option("--json", "json_output", is_flag=True, help="Write machine-readable JSON to stdout.")
@click.version_option(__version__)
@click.pass_context
def cli(ctx: click.Context, project: Path, root: Path | None, verbose: int, quiet: bool, json_output: bool) -> None:
    """Inspect and build OntoSpreadEd projects using ose-lib."""
    if verbose and quiet:
        raise click.UsageError("--verbose and --quiet are mutually exclusive")
    ctx.obj = Options(project, root, verbose, quiet, json_output)
    logging.basicConfig(level=logging.DEBUG if verbose else logging.ERROR if quiet else logging.WARNING)


@cli.group()
def project() -> None:
    """Inspect project configuration and spreadsheet schemas."""


@project.command("show")
@click.pass_obj
@command_errors
def project_show(options: Options) -> None:
    p = options.load_project()
    order = graphlib.TopologicalSorter({name: f.needs for name, f in p.files.items()}).static_order()
    files = {"external": p.external, **{name: p.files[name] for name in order}}
    data = dict(
        short_name=p.short_name,
        full_name=p.full_name,
        iri_prefix=p.iri_prefix,
        files={k: f.model_dump(mode="json") for k, f in files.items()},
        build_configurations=[c.model_dump(mode="json") for c in p.build_configurations],
    )
    lines = [f"{p.short_name}: {p.full_name}", f"IRI prefix: {p.iri_prefix}"]
    lines += [
        f"{k}: {', '.join(s.file for s in f.sources)} → {f.target.file} (needs: {', '.join(f.needs) or '-'})"
        for k, f in files.items()
    ]
    lines += [f"Build {c.name}: {', '.join(s.name for s in c.stages)}" for c in p.build_configurations]
    options.emit(data, lines)


@project.command("check")
@click.pass_obj
@command_errors
def project_check(options: Options) -> None:
    p = options.load_project()
    errors = []
    for name, f in {"external": p.external, **p.files}.items():
        for path in [*(s.file for s in f.sources), f.renameTermFile, f.addParentsFile]:
            if path and not (options.root / path).is_file():
                errors.append(f"{name}: missing file {path}")
    options.emit(dict(valid=not errors, errors=errors))
    if not options.json:
        for error in errors:
            options.error(error)
        if not errors:
            options.info("Project configuration and referenced files are valid.")
    if errors:
        raise click.exceptions.Exit(1)


@project.command("schema")
@click.argument("name", required=False)
@click.pass_obj
@command_errors
def project_schema(options: Options, name: str | None) -> None:
    p = options.load_project()
    schemas = BUILTIN_SCHEMAS | p.spreadsheet_schemas
    if name:
        # Resolved schemas are always JSON, also without the global --json flag.
        click.echo(resolve_schema(name, schemas).model_dump_json(indent=2))
    else:
        data = {
            k: dict(builtin=k in BUILTIN_SCHEMAS and k not in p.spreadsheet_schemas, extends=s.extends)
            for k, s in schemas.items()
        }
        options.emit(
            data,
            [
                f"{k} ({'builtin' if s['builtin'] else 'project'}, extends: {s['extends'] or '-'})"
                for k, s in data.items()
            ],
        )


@cli.command("stages")
@click.pass_obj
@command_errors
def stages(options: Options) -> None:
    """List discovered stages and their required build contexts."""
    data = []
    for name, cls in available_stages().items():
        context = stage_context(cls)
        data.append(
            dict(
                name=name,
                module=cls.__module__,
                context=f"{context.__module__}.{context.__name__}",
                runnable=issubclass(BuildContext, context),
            )
        )
    options.emit(
        data,
        [
            f"{s['name']}: {s['module']} (context: {s['context']}, CLI: {'yes' if s['runnable'] else 'no'})"
            for s in data
        ],
    )


cli.add_command(build)


@cli.command("validate")
@click.argument("files", nargs=-1)
@click.option("--only", multiple=True, type=click.Choice(list(dict.fromkeys(get_args(DIAGNOSTIC_KIND)))))
@click.option("--exclude", multiple=True, type=click.Choice(list(dict.fromkeys(get_args(DIAGNOSTIC_KIND)))))
@click.pass_obj
@command_errors
def validate(
    options: Options, files: tuple[str, ...], only: tuple[DIAGNOSTIC_KIND, ...], exclude: tuple[DIAGNOSTIC_KIND, ...]
) -> None:
    """Validate the project; FILE arguments select report keys, not input paths."""
    p = options.load_project()
    unknown = set(files) - (set(p.files) | {"global"})
    if unknown:
        raise click.UsageError(f"Unknown file keys: {', '.join(sorted(unknown))}")
    start_build(
        options,
        stages=("VALIDATION",),
        stage_args={"only": list(only) or None, "exclude": list(exclude) or None},
        report_files=files,
    )


@cli.command("externals")
@output_options
@click.pass_obj
@command_errors
def externals(options: Options, out: Path | None, write: bool) -> None:
    """Build external imports (writes to the project unless --out is given)."""
    start_build(options, stages=("EXTERNAL_IMPORTS",), out=out, write=write or out is None)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
