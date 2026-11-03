# OSE Plugin: BCIO

OntoSpreadEd plugin for BCIO (Behaviour Change Intervention Ontology) services and workflows.

## Description

This plugin extends OntoSpreadEd with functionality specific to the BCIO ontology project. It provides:

- BCIO search build stage for automated release pipelines
- Custom scripts for BCIO vocabulary management:
  - Clean up BCIO vocabulary
  - Import missing external terms
  - Update imports to latest versions
  - Set pre-proposed curation status
- Integration with BCIO search services
- Custom UI components for BCIO-specific workflows

## Installation

```bash
pip install ose-plugin-bcio
```

## Requirements

- Python 3.13+
- ose-lib
- ose-plugin-hbcp

## Configuration

The plugin is automatically discovered and loaded when installed. Register it in your release script to use BCIO-specific build stages and scripts.

## License

LGPL-3.0-or-later

## Discovery

The `ose.build_stages` group exposes `BCIO_SEARCH` to the app and standalone CLI.
Arguments stay in the stage’s `args` mapping; inputs are read from the build directory.
The `ose.web_plugins` group exposes the lazy release view through `definePlugin`.
See [plugin configuration](../README.md#search-service-settings) for API URL and token settings.
The four scripts are discovered through `ose.scripts` and require `ose-app`.

Known existing script defects: `import_missing_externals` has its actual update commented
out and hardcodes `addicto_external.owl`; `cleanup_bcio_vocab` writes files into the working directory.
