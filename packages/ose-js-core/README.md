# OSE JS Core

Core TypeScript library for OntoSpreadEd - shared types, models, and utilities.

## Description

This package provides TypeScript type definitions, models, and utility functions shared across OntoSpreadEd frontend components. It includes:

- TypeScript interfaces for ontology entities
- Shared constants and configuration types
- Utility functions (debounce, filtering, etc.)
- Diagnostic and validation data structures

## Installation

```bash
npm install @ontospreaded/js-core
```

## Requirements

- Node.js 20.19+ (required by Vite 7)
- Vue 3 (peer dependency)

## Build

```bash
npm run build
```

## License

LGPL-3.0-or-later

## Plugin API

Default-export `definePlugin({apiVersion: 1, setup(ose) { ... }})`. The context provides
`id` and `release.addStageView(stageName, component | loader, options?)`. Exported contracts include
`PLUGIN_API_VERSION`, `PluginContext`, `PluginDefinition`, `StageViewOptions`, `StageViewProps<Data>` and
`ReleaseControlEmit`. The host uses `setupPlugin`, `registry.stageView(name)` and
`registry.stageViewOptions(name)`.

```ts
export default definePlugin({
  apiVersion: 1,
  setup(ose) {
    ose.release.addStageView("EXAMPLE", () => import("./Example.vue"));
  },
});
```

See [plugin guide](../../plugins/README.md) for discovery, ordering, overrides and builds.
