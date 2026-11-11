# Plugins for OntoSpreadEd

Install plugins as Python packages. Each extension type has its own entry point group;
there is no `ose.plugins` group or combined Python plugin object.

| Group | Entry point value | Consumer |
| --- | --- | --- |
| `ose.build_stages` | Module containing concrete `ose.building.stages.BuildStage` subclasses | Library, CLI and app |
| `ose.scripts` | Module containing concrete `ose_app.model.Script` subclasses | App; instances use the injector |
| `ose.web_plugins` | `ose_app.model.WebPlugin` instance | App and SPA |

```toml
[project.entry-points.'ose.build_stages']
example = "example.stages"

[project.entry-points.'ose.scripts']
example = "example.scripts"

[project.entry-points.'ose.web_plugins']
"org.example.plugin" = "example.web:WEB_PLUGIN"
```

```python
# example/web.py
from ose_app.model import WebPlugin
WEB_PLUGIN = WebPlugin(module="example.js", static_folder="static")
```

The web plugin id is the entry point name. Static files are relative to the entry
point module. Python only declares the bundle location; UI extensions belong in JS.
`GET /api/plugins/` is public and returns `{id, type, distribution, version}`
objects for every successfully loaded entry point across all plugin types. The `type`
is the entry point group; `(type, id)` identifies a row. Only web-plugin entries include
`module_url`. The admin dashboard lists these entries with their distribution and
version. Distribution metadata comes from the installed package. `module_url` is an
absolute path relative to the app's URL prefix; the frontend prepends its configured
prefix. Files are served at `/api/plugins/<id>/static/<path>`.

## JavaScript API

```ts
import {definePlugin} from "@ontospreaded/js-core";

export default definePlugin({
  apiVersion: 1,
  setup(ose) {
    ose.release.addStageView("EXAMPLE", () => import("./Example.vue"));
  },
});
```

`definePlugin` provides types and returns its argument. `PLUGIN_API_VERSION` is 1.
`PluginContext` supplies `id` and `release.addStageView(name, component | loader, options?)`.
Bare functions are treated as loaders; wrap functional Vue components with
`defineComponent`. `StageViewProps<Data>` describes `data`, `release` and
`selectedSubStep`; `ReleaseControlEmit` describes the `release-control` event.
Stage views are read through `registry.stageView(name)` with a generic fallback.

The app lists a stage's warnings and infos below its view. A view that lists them itself
passes `{showsDiagnostics: true}` as `options` (`StageViewOptions`, read through
`registry.stageViewOptions(name)`); the built-in `VALIDATION` view does.

Before mounting, the SPA registers built-in views, fetches plugins, filters to entries
with a `module_url`, imports them in
id order, checks the API version, and awaits setup. Failures are logged and skipped.
Setup registrations are committed only on success. Later registrations override
previous ones and log a warning, including overrides of built-ins.

Build with Vite library mode, ES output, and `vue` / `@ontospreaded/js-core` as
externals. Lazy component imports produce sibling chunks whose paths resolve
relative to the entry module. Include all chunks in package data. Runtime importmaps
use generated shims for the host's Vue and JS-core instances. Plugin CSS loading,
activation manifests and inter-plugin services are outside this API.

## Build stages

Stages take `(step_config, context)` and read arguments from `self.config.args`.
Implement async `run(on_progress_update=None)`, returning `ose.result.Result`.
Use `ProgressManager` and `check_cancelled()`, read files from `context.build_dir`,
and register outputs through `context.add_final_artifact`. They must not depend on
Flask or app services. `ose stages` lists all installed stages.

## Search service settings

BCIO and AddictO use `OSE_PLUGINS__BCIO__API_PATH` and
`OSE_PLUGINS__ADDICTO__API_PATH`, defaulting to `https://api.bciosearch.org/` and
`https://api.addictovocab.org/`. Set the corresponding `API_AUTH_TOKEN` variables
for authentication. Flask forwards nested YAML/JSON settings into these variables;
environment settings take precedence:

```yaml
plugins:
  BCIO:
    API_PATH: https://api.bciosearch.org/
    API_AUTH_TOKEN: your-token
```

The release runner loads the same configuration; standalone CLI builds use the
environment directly. HBCP is a shared library with no entry points.
