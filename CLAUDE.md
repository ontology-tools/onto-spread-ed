# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**OntoSpreadEd** (Ontology Spreadsheet Editor) is a Python/TypeScript monorepo for collaborative editing of OWL ontologies
through spreadsheet interfaces. It enables domain experts to work with complex ontologies using familiar Excel-like views
without requiring deep OWL syntax knowledge.

The branch `feature/refactor-extract-library` is an ongoing refactoring: extract a reusable, Flask-free ontology library
(`ose-lib`, imported as `ose`), turn Flask into a JSON API behind a Vue SPA, and run releases in a separate process. See
[Refactoring status](#refactoring-status) for what is done and what is still open.

## Repository Structure

```
onto-spread-ed/
├── packages/
│   ├── ose-lib/            # Python: core library, import name `ose` (project config, schemas, ontology, builds)
│   ├── ose-app/            # Python: Flask backend (JSON API, OAuth, release runner, serves the SPA)
│   ├── ose-cli/            # Python: `ose` command-line interface over ose-lib (no Flask needed)
│   ├── ose-js-core/        # TypeScript: shared types, build model mirror, plugin API, release components
│   └── ose-js-app/         # TypeScript/Vue: the single-page web app
├── plugins/
│   ├── ose-plugin-addicto/                    # AddictO: vocab/search stage + web plugin
│   ├── ose-plugin-bcio/                       # BCIO: search stage, web plugin and scripts
│   ├── ose-plugin-hbcp/                       # Shared HBCP search-service library (no entry points)
│   ├── ose-plugin-hierarchical-spreadsheets/  # Hierarchical spreadsheet export stage
│   └── ose-plugin-annotation-sheets/          # Annotation sheet template stage
├── scripts/generate-shims.mjs  # Generates the Vue / js-core shims for plugins
├── app.py, config.yaml         # Root WSGI entry point and local app configuration
└── .github/workflows/CI.yaml
```

## Technology Stack

- **Python 3.13+**: Flask, Flask-SQLAlchemy/Migrate, Flask-Injector, pydantic, py-horned-owl, Whoosh, openpyxl,
  networkx, PyGithub + GitPython (not flask_github)
- **TypeScript/Vue 3**: Vite, vue-router, Bootstrap / bootstrap-vue-next, Tabulator.js, D3.js
- **Build tools**: uv workspace (Python), npm workspaces (JS), Make
- **Linting**: ruff (Python), vue-tsc (TypeScript), mypy (`make type-check`, not in CI)

## Common Commands

```bash
# Installation
make install          # npm install + uv sync --all-packages --all-groups
make install-js / make install-python

# Building (order matters, see Important Notes)
make build            # build-js + build-python
make build-js         # npm run build (js-core -> shims -> js-app) + JS plugins
make build-python     # uv build for every package and plugin (requires build-js)
make build-prod       # clean build, keeps only publishable wheels in dist/

# Development
make dev              # vite on :5173, Flask on :5000 and the release runner; open http://localhost:5173
npm run dev           # only vite (builds js-core + shims first, proxies /api etc. to Flask :5000)
make dev-python       # only Flask (flask --app ose_app:create_app run --debug --port 5000)
make dev-release-runner  # only the release runner (flask --app ose_app:create_app release-runner)
npm -w @ontospreaded/js-app run watch  # old `vite build --watch` flow (then open Flask on :5000)

# Database
make db-upgrade       # flask --app ose_app:create_app db upgrade
make db-migrate       # create a new migration

# Linting, types, tests
make lint             # uv run ruff check packages/ plugins/
make lint-python-fix  # ruff --fix
make type-check       # mypy packages/ and plugins/
make test             # pytest (testpaths: tests, packages/*/tests)
npx vue-tsc -p packages/ose-js-app/tsconfig.json --noEmit         # same check as CI; also ose-js-core/tsconfig.app.json
node --test packages/ose-js-core/tests                             # JS plugin registry tests (needs built js-core dist)

# CLI
uv run ose --help     # project show/check/schema, stages, build, externals, validate (see packages/ose-cli/README.md)

# Cleaning
make clean / make clean-all   # clean-all also removes node_modules and .venv
```

When running pytest manually, prefer `.venv/bin/pytest -q -p no:cacheprovider <paths>` and bound long runs with
`timeout` (the release-runner tests use asyncio and earlier stalled during teardown).

## Architecture

### Web app

The web UI is a single Vue 3 SPA (`packages/ose-js-app`: `index.html` + `src/main.ts`, vue-router in history mode).
There are no server-rendered pages.

- Flask (`ose-app`) serves only `/api/*`, the OAuth routes (`/login`, `/logout`, `/github-callback`), `/status` and static files.
- `routes/spa.py` is the catch-all (registered last) that serves the SPA. It reads `static/app/index.html`, injects
  `window.OSE_CONFIG = {prefix}` and the importmap at the `<!--ose-head-->` marker, and rewrites the relative asset URLs
  (`="./`) to `{URL_PREFIX}/static/app/`. `URL_PREFIX` is therefore a runtime setting. There is no `<base>` tag; the
  router base comes from `OSE_CONFIG.prefix` (`src/config.ts`).
- `/api/*` never redirects or renders HTML: auth failures are always JSON `401`/`403` (`{success: false, error}`);
  GitHub unauthorized errors are handled centrally for all API routes.
- Page data comes from the JSON API blueprints in `routes/api/`. `/api/me` provides the user, permissions and app info.
  There is no separate API reference file; documentation belongs in the docs.
- Project settings saves use revision/`If-Match` conflict checks against the current GitHub content and preserve
  unknown (extension) fields of `.onto-ed/config.yaml` (`routes/api/settings.py`, `utils/config_file.py`).
- Frontend internals (routes, `api()` helper, layout state incl. `fillHeight` route meta, adding a page):
  `packages/ose-js-app/README.md`.

### Builds and stages

A build runs a configured sequence of `BuildStage`s (`ose.building.run`) over a `BuildContext`. Each stage has a
`name()` and an async `run()` returning a `Result[StageResult]`; `StageResultType` (`"skipped" | "cancelled" | "paused"`,
optionally with data) lets stages control the run. Builtin stages are discovered automatically by inspection; plugin
stages come from the `ose.build_stages` entry points.

- Library stages (`ose.building.stages`): `EXTERNAL_IMPORTS`, `VALIDATION`, `EXCEL2OWL`, `MERGE`.
- App release stages (`ose_app.release.stages`, `ReleaseContext` with the user's GitHub token):
  `PREPARATION` (clones the repository into the release's own build directory), `HUMAN_VERIFICATION`,
  `GITHUB_PUBLISH`, `CLEANUP`. Publishing never cleans up; cleanup only happens in the configured `CLEANUP` stage
  (cancelled builds keep their files and branches unless cleanup was already reached).
- Ontology building goes through the `OntologyBuildService` ABC (`RobotOntologyBuildService`,
  `HornedOntologyBuildService`; the Horned implementation is incomplete). ROBOT work uses temporary directories and a
  download/extraction cache (`OSE_ROBOT_CACHE_DIR`, `OSE_ROBOT_CACHE_MAX_AGE`).
- The CLI runs the same stages; stages that need an application context such as `ReleaseContext` are skipped there.

### Release runner

Releases run in a separate process, `flask --app ose_app:create_app release-runner` (`release/runner.py`,
`release/cli.py`), exactly one per database. In production (uwsgi with several workers) it is supervised via
`attach-daemon2`, with Gunicorn via a systemd service.

- The API and the runner only communicate through the `releases` table: the API records requests (`requested_action`,
  `requested_by` = GitHub username) and cancels by setting `state = 'cancelled'` (sticky); the runner claims releases
  (`worker_id` lease), refreshes `heartbeat_at`, and is the only writer of the remaining state.
- Releases of stale runners are taken over and marked as interrupted; on `SIGTERM` running releases are interrupted and
  can be rerun.
- Releases of different repositories run in parallel (`RELEASE_MAX_PARALLEL`, default 2), but a partial unique index
  allows only one open release per repository. Don't reintroduce per-repo waiting/locking or PID-based liveness.
- Timings are app settings: `RELEASE_POLL_INTERVAL`, `RELEASE_HEARTBEAT_INTERVAL`, `RELEASE_LEASE_TIMEOUT`,
  `RELEASE_PROGRESS_INTERVAL` (`default_config.py`).
- Each release clones the repository into its own build directory, so releases share no git state.

### Plugin system

Each extension type has its own Python entry point group (there is no `ose.plugins` group or combined plugin object):

- `ose.build_stages`: a module scanned for concrete `ose.building.stages.BuildStage` subclasses; discovered by the
  library, CLI and app.
- `ose.scripts`: a module scanned for concrete `ose_app.model.Script` subclasses, instantiated through the app injector.
- `ose.web_plugins`: a typed `ose_app.model.WebPlugin(module="plugin.js", static_folder="static")`. Its id is the entry
  point name and its static directory is relative to the entry point module; files are served at
  `/api/plugins/<id>/static/<path>`.

`PluginService` discovers scripts and web plugins and records build-stage entry points. The public `/api/plugins/`
endpoint returns `{id, type, distribution, version}` for all loaded entry points, with an optional `module_url` for web
plugins. The admin dashboard lists these entries; the SPA loader only imports entries with a `module_url`.

HBCP is a shared library without entry points. Search stages use `OSE_PLUGINS__BCIO__API_PATH` /
`OSE_PLUGINS__ADDICTO__API_PATH` and the corresponding `API_AUTH_TOKEN` environment variables; Flask forwards nested
`PLUGINS` configuration into those variables. Hierarchy support lives in `ose.ontology.hierarchy`. Full examples and
contracts: `plugins/README.md`.

### Plugin loading (frontend)

Plugin bundles use Vite ES library output with `vue` and `@ontospreaded/js-core` as externals. Generated shims expose
`window.Vue` and `window.OseJsCore` through the importmap. Before mounting, `main.ts` registers built-in release views,
fetches `/api/plugins/`, then imports plugins in id order and calls their version-checked setup. JS modules
default-export `definePlugin({apiVersion: 1, setup(ose) {...}})`. Failed plugins are logged and skipped. Plugins register
lazy stage components through `ose.release.addStageView`; later registrations win with a warning. `Release.vue` reads
the shared registry.

## Package Dependencies

```
ose-lib ──┬──► ose-cli
          ├──► ose-app ─────────────► ose-plugin-bcio (scripts need ose-app)
          ├──► ose-plugin-hbcp ──┬──► ose-plugin-bcio
          │                      └──► ose-plugin-addicto
          ├──► ose-plugin-hierarchical-spreadsheets
          └──► ose-plugin-annotation-sheets

ose-js-core ──► ose-js-app
            └─► JS plugins (addicto, bcio)
```

`ose-lib` must not depend on Flask or `ose_app`. `ose-cli` is optional for `ose-app` (`ose-app[cli]`).

## Key Directories

### Python
- `packages/ose-lib/src/ose/` - `project.py` (project config model), `schema/`, `ontology/` (`ExcelOntology`,
  `hierarchy`, `loading`), `building/` (`run.py`, `BuildContext`, build services, `stages/`), `result.py`, `utils/`
- `packages/ose-app/src/ose_app/`
  - `routes/` - `api/` (JSON API blueprints), `auth.py`, `status.py`, `spa.py` (catch-all)
  - `release/` - `runner.py`, `cli.py`, `stages.py`
  - `database/` (models + `migrations/`), `services/`, `guards/`, `model/`, `index/`, `utils/` (`git`, `github`, `config_file`)
  - `default_config.py` - app settings and defaults; `AppModule.py` - injector bindings
  - `static/app/` - built SPA (output of the `ose-js-app` build; git-ignored)
- `packages/ose-cli/src/ose_cli/` - Click commands (`main.py`, `build.py`, `diagnostics.py`, `common.py`)
- Tests: `packages/*/tests/` (`ose-lib`: builds, ROBOT, asyncio, plugin stages; `ose-app`: runner, release CLI,
  settings, plugins; `ose-cli`)

### TypeScript
- `packages/ose-js-core/src/` - `model.ts` (mirror of the ose-lib build model), `plugins/`, `release/`, shared utilities
- `packages/ose-js-app/src/` - Vue SPA (`main.ts`, `App.vue`, `router.ts`, `api.ts`, `config.ts`, `state.ts`, `plugins.ts`)
  - `pages/` (Home, Repo, LoggedOut, NotFound), `admin/`, `settings/`, `editor/`, `release/`, `visualise/`, `common/`
- `packages/ose-js-app/public/` - generated shims (`vue-shim.js`, `ose-js-core-shim.js`)

## Configuration

- App configuration: `config.yaml` (root, loaded by `app.py`) plus `OSE_*` environment variables; see the README table.
  `startup-repositories.yaml` preloads repositories (git-ignored); local clones go to `repositories/` (git-ignored).
- Ontology repositories describe themselves in `.onto-ed/config.yaml` (files, `needs`, prefixes, validation,
  `build_configurations`); the model is `ose.project.Project`.
- `pyproject.toml` - uv workspace; `package.json` - npm workspaces; `ruff.toml` - ruff rules (takes precedence over
  `[tool.ruff]` in `pyproject.toml`); `tsconfig.json` / `vite.config.ts` per JS package.

## CI/CD

`.github/workflows/CI.yaml` (Python 3.13, Node 20):
- **Lint**: ruff, vue-tsc for js-core, js-app and the JS plugins (type errors fail the check). Tests are not run in CI.
- **Build**: `make install-js install-python build-js build-python`, uploads wheels and sdists.
- **Publish** on release: everything in `dist/` to PyPI (intended: ose-lib, ose-app, ose-cli and the hierarchical-spreadsheets / annotation-sheets plugins, see `make build-prod`) and all public npm workspaces (intended: `@ontospreaded/js-core`).
- **Deploy**: dev/prod environments.

## Code Style and Design Principles

- Python: line length 120, ruff rules E4, E7, E9, F, target Python 3.13. Use absolute imports (`ose.…`, `ose_app.…`);
  never convert them to relative imports.
- TypeScript/Vue: strict mode, no unused locals/parameters, single-file components.
- Keep the extension points the architecture is built on, even if only one implementation exists today: ABCs such as
  `OntologyBuildService` and `BuildStage`, automatic (`inspect`/entry point) discovery instead of hand-maintained lists,
  and `StageResultType` control for stages. "Minimal" applies to new code, not to removing these.
- Prefer typed constructors/models over factories taking `**kwargs`.
- Each lifecycle concern gets its own step (e.g. a `CLEANUP` stage rather than publish deleting the build directory).
- Change only what the agreed plan names. Any other API change (signatures, endpoints, config keys, removed/added
  methods, behaviour) must be asked about first or at least listed explicitly.

## Important Notes

1. **Build order**: js-core -> shims (into `ose-js-app/public`) -> js-app (-> `ose_app/static/app`) -> JS plugins ->
   Python wheels. `npm run build` covers the first three, `make build-js` adds plugins. JS must be built before Python
   packages (static assets are included in the wheels). Without the SPA build, every non-API page answers with an error.
2. **Workspace dependencies**: use `workspace = true` in `[tool.uv.sources]` for local packages.
3. **Plugin static assets**: plugin JS/CSS goes in `src/<plugin_package>/static/`.
4. **Dev workflow**: `make dev`, then open http://localhost:5173 (use `localhost`, not `127.0.0.1`). Vite injects
   `OSE_CONFIG` and the importmap itself and proxies `/api`, `/login`, `/logout`, `/github-callback`, `/status` and
   `/static` to Flask on :5000 (override with `FLASK_PORT`). `OSE_DEV_PORT` and `OSE_DEV_SSL_CERT`/`OSE_DEV_SSL_KEY`
   change Vite's port and enable HTTPS. The VS Code compound launch config "OSE: Dev (Flask debugger + Vite)" (F5) runs
   Flask under the debugger on plain HTTP :5000 and Vite on https://localhost:8080 with `ssl/cert.pem`/`ssl/key.pem`, so
   the GitHub OAuth callback on :8080 reaches Flask through Vite.
5. **Database migrations**: `flask --app ose_app:create_app db upgrade`. Add a migration for every model change.
6. **Persisted releases** store their build context; changes to `BuildContext`/`ReleaseContext` or artifact schemas must
   stay compatible with releases already in the database.

## Refactoring Status

Last verified **2026-11-03**. Keep this section current: when work is implemented and verified, update it with the
check that proves it. Mark an item done only with evidence.

### Done (committed)

- Library extraction into `ose-lib` (no Flask/`ose_app` imports), `ose-core` -> `ose-lib` rename.
- Flask JSON API + Vue SPA with runtime URL prefix and importmap; project settings editor with dependency graph and
  conflict-checked saves.
- Separate DB-backed release runner with migration `d41f6e2a8c55_release_runner`; per-release clones; cleanup only via
  the `CLEANUP` stage.
- Build isolation, ROBOT caching, local ontology IRI-to-file mappings, thread-safe cancellation.
- CLI rewritten over ose-lib (`ose project|stages|build|externals|validate`); `ose --help` works.
- Plugins moved to the three entry point groups; versioned JS `definePlugin` API with lazy stage views; admin plugin list.
- flask_github replaced by PyGithub; central GitHub unauthorized handling. `users.github_id` is required (model and
  migration `abc5f3fb8860`, which deletes users without one).
- Version 2.0.0 for all Python and JS packages.
- VALIDATION intentionally skips files whose sources are all OWL: in BCIO these are outputs of other project files that
  do not exist yet (or are stale) when VALIDATION runs before EXCEL2OWL.

### Verification baseline (2026-11-03, local Python 3.14)

Passing:
- `ruff check packages/ plugins/`, `vue-tsc` for js-core and js-app (JS plugins passed earlier the same day).
- `pytest`: 254 passed in ~11 s.
- `make build-python` (includes `build-js`): all wheels/sdists build; `ose-app` contains the SPA, shims and all
  migrations, the JS plugins contain their bundle plus lazy chunks, `ose-lib` contains `py.typed` and schemas.
  Only Sass deprecation warnings. (Run before the 2.0.0 bump.)
- Migrations on a fresh SQLite DB: `upgrade` -> `downgrade base` -> `upgrade`; `abc5f3fb8860` up/down with a
  `NULL` `github_id` row (deleted on upgrade, NOT NULL enforced afterwards).
- Local app smoke test (no login): `/status/`, anonymous `/api/me`, JSON `401` on `/api/release/`, JSON `404` on unknown
  `/api/*`, SPA on deep links, both plugin bundles served from `/api/plugins/<id>/static/...`.

Failing (independent of the refactoring, see below): `make type-check`, `flask db check`.

### Open work

Baseline for "caused by the refactoring" is `origin/main` = `2cacce7` (2026-07-30), the last commit before the library
extraction. Local `main` (`81a5027`) already contains the first refactoring commits.

#### Caused by the refactoring (finish before merging)

- [ ] `packages/ose-lib/README.md` is empty and its `pyproject.toml` description is a placeholder.
- [ ] Deployment: the servers' `redeploy` script (outside this repo) must replace `ose-core` by `ose-lib`, use Python 3.13,
  run `db upgrade` (`9c1e4b2f7a30`, `d41f6e2a8c55`, `abc5f3fb8860`), rename the BCIO/AddictO API settings to
  `OSE_PLUGINS__*`, and run exactly one release runner sharing `/tmp` with the web workers.
- [ ] Manual verification (needs GitHub OAuth and a test repository): login/logout, permissions, repository browsing,
  spreadsheet editing/saving, search/visualisation, settings saves with conflicts, plugin release views; a full release
  (preparation -> human verification -> publish -> cleanup) plus runner cancellation, restart, stale-worker takeover,
  pause/continue, rerun/skip and parallel releases; upgrading a database with open/duplicate releases.

#### Independent issues (existed before or outside the refactoring's scope)

- [ ] BCIO scripts, identical at `2cacce7`: `import_missing_externals` has its update commented out and hardcodes
  `addicto_external.owl`; `cleanup_bcio_vocab` writes `ids.json` / `to_be_deleted.xlsx` into the working directory.
- [ ] CI publishes everything in `dist/` and `npm publish --workspaces` includes `@ontospreaded/js-app`, as at `2cacce7`.
  `make build-prod` (keeps ose-app/cli/lib and the hierarchical-spreadsheets / annotation-sheets plugins) is not used by CI.
- [ ] Root README: `pip install -r requirements.txt` and `flask run db upgrade` are wrong, as at `2cacce7`.
- [ ] `URL_PREFIX` only affects generated URLs; routes are registered at the root, so the reverse proxy must strip the
  prefix. Unchanged since `2cacce7`, but undocumented.
- [ ] `flask db check` / `make db-migrate`: models use `database/Base.py`'s own `DeclarativeBase`, Flask-Migrate compares
  against `db.metadata`, so autogenerate would drop all tables. Unchanged since before `2cacce7`.
- [ ] `make type-check`: mypy aborts with "Duplicate module" because of `packages/*/build/lib` from `uv build`; target
  and build layout are unchanged since `2cacce7`.
- [ ] `tests/excel_ontology.test.py` (from e402023) is never collected because of its file name; it now also imports the
  removed `ose.model`. `tests/smoke/` and `tests/system/` are untracked local directories with only `__pycache__`.
- [ ] `PermissionManager` raises `KeyError` (500 on every permission check) when `permission-groups` is missing from the
  config; unchanged since `2cacce7`.

#### Deferred follow-ups

- [ ] `HornedOntologyBuildService.merge_imports` / `collapse_imports` raise `NotImplementedError` (fix later).
- [ ] Conditions in the ose-lib build configuration so `CLEANUP` can also run after cancel/error.
