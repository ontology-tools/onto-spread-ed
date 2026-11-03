# OSE Plugin: AddictO

OntoSpreadEd plugin for AddictO (Addiction Ontology) services and workflows.

## Description

This plugin extends OntoSpreadEd with functionality specific to the AddictO ontology project. It provides:

- AddictO vocabulary build stage for automated release pipelines
- Integration with external AddictO vocabulary services
- Custom UI components for AddictO-specific workflows

## Installation

```bash
pip install ose-plugin-addicto
```

## Requirements

- Python 3.13+
- ose-lib
- ose-plugin-hbcp

## Configuration

The plugin is automatically discovered and loaded when installed. Register it in your release script to use the AddictO vocabulary step.

## License

LGPL-3.0-or-later

## Discovery

The `ose.build_stages` group exposes `ADDICTO_VOCAB` to the app and standalone CLI.
Arguments stay in the stage’s `args` mapping; inputs are read from the build directory.
The `ose.web_plugins` group exposes the lazy release view through `definePlugin`.
See [plugin configuration](../README.md#search-service-settings) for API URL and token settings.
