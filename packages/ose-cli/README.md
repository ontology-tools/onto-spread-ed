# OSE CLI

Standalone project inspection and ontology builds over `ose-lib`. Python 3.13+ is
required. Install with `pip install ose-cli`; Flask and `ose-app` are optional.
ROBOT stages require Java and a ROBOT executable (`ROBOT` can select its path).

## Project commands

The default configuration is `.onto-ed/config.yaml`. `--project` / `-p` accepts a
configuration file or a project directory. Paths inside the configuration are
relative to the project root (the parent of `.onto-ed`, or the configuration's
own directory for other locations). `--root DIR` overrides that root.

```sh
ose project show
ose project check
ose project schema
ose project schema default
ose stages
ose -p /path/to/project --json project show
```

`show` lists files in dependency order, including sources, targets and `needs`,
plus named build configurations. `check` validates the configuration and checks
all source, rename and parent files; problems exit with status 1. `schema` lists
builtin and project schemas with their `extends`; a schema name prints its
resolved JSON. `stages` discovers builtins and `ose.build_stages` plugins and
shows their module, required context and whether the CLI can run them.

Result diagnostics use colored ERROR (red), WARNING (yellow) and INFO (cyan)
labels, with the file, row, entity and relevant details. Build states are colored
green on success, yellow when waiting or skipped, and red on failure. Color is
automatically omitted when output is redirected. Saved build status uses the
same diagnostic formatting.

Global `-v` enables debug messages, tracebacks and progress; `-q` shows only
errors. They are mutually exclusive. `--json` emits one JSON document on stdout,
including structured result logs, with progress and notices on stderr. Place
global options before the command.

## Builds

```sh
ose build release
ose build --stage EXTERNAL_IMPORTS --stage VALIDATION --stage EXCEL2OWL --stage MERGE
ose build release --skip VALIDATION --out ./output
ose build release --build-dir ./build --robot-cache /path/to/cache
ose build release --write
ose build release --in-place
```

Omit CONFIG to use the `default` configuration, or the sole configuration if
there is only one. Otherwise specify a name. Repeated `--stage NAME` creates an
ad-hoc configuration in the specified order and cannot be combined with CONFIG.
Repeated `--skip NAME` removes stages, including configured stages whose plugins
are not installed. Stages requiring an application context such as
`ReleaseContext` are skipped with a notice and recorded in the saved metadata.

By default, builds copy the project tree to a temporary directory, excluding
`.git` and CLI state files. Configuration paths must stay inside that tree.
`--build-dir DIR` uses an empty directory of your choice; a directory inside the
project is supported and excluded from its own copy. `--in-place` runs directly
in the project root and implies `--write`; it excludes `--build-dir`.

After success, `--out DIR` copies each final artifact to `DIR/<final_path>`;
`--write` copies the same artifacts back to the original project. Both may be
used together. Only final artifacts are published, and relative paths are
preserved. Temporary builds are removed after success unless `--keep` is given.
Explicit build directories and in-place builds are retained. Failure, pause or
interruption always retains the build directory; its path is printed on stderr.
Builds that stop before completion exit with status 1.

`--robot-cache DIR` temporarily sets `OSE_ROBOT_CACHE_DIR` and is saved for
resume. The library also honors `OSE_ROBOT_CACHE_MAX_AGE`.

## Saved builds

```sh
ose build status ./build
ose --json build status ./build
ose build resume ./build
ose build resume ./build --skip-current --out ./output --write
```

The build context and CLI metadata are saved atomically in
`<build_dir>/.ose-build.json` before execution, during progress and after each
stage. Status includes state, per-stage results, error/warning counts and
artifacts. Resume uses the saved project and original project root, so it does
not require a configuration in the current working directory. Keep the build
directory at its saved absolute location.

Failed or cancelled stages are retried; paused stages continue at the following
stage, matching `BuildContext.next_stage()`. `--skip-current` skips the saved
current stage. Output and write settings persist unless a new `--out` is passed;
`--write` also enables publication on resume. A temporary build still follows
its original `--keep` setting after a successful resume. An unfinished in-place
build must be resumed or its state file moved before starting a new build.

## Validation and external imports

```sh
ose validate
ose --json validate terms global
ose validate --only duplicate --exclude no-parent
ose externals
ose externals --out ./output
```

`validate` runs the VALIDATION stage and prints its per-file report, including
failed files. FILE arguments select project file keys (or `global`) for display;
the whole project is still validated so dependencies and global checks remain
available. `--only KIND` and `--exclude KIND` are repeatable diagnostic filters
passed to ontology validation. Input parsing and resolution errors still fail
the build. Reports, logs and the failed build remain available for inspection.
OWL-only targets are reported as skipped during spreadsheet validation: they
are assembled later by MERGE. Ambiguous label references produce warnings;
include an explicit ID to resolve them unambiguously.

`externals` runs EXTERNAL_IMPORTS and writes final artifacts back to the project
by default. With `--out DIR`, publication goes to DIR; add `--write` to publish
to both places. This replaces `ose externals build -r release_script.json`;
configure external sources and targets in `.onto-ed/config.yaml` instead.
The old empty `release` group is replaced by `build`; web release management
remains in `ose-app`.

## License

LGPL-3.0-or-later
