# OSE Plugin: BCIO

OntoSpreadEd plugin for BCIO (Behaviour Change Intervention Ontology) services and workflows.

## Description

This plugin extends OntoSpreadEd with functionality specific to the BCIO ontology project. It provides:

- BCIO search release step for automated release pipelines
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

- Python 3.12+
- ose-core
- ose-plugin-hbcp

## Configuration

The plugin is automatically discovered and loaded when installed. Register it in your release script to use BCIO-specific release steps and scripts.

## License

LGPL-3.0-or-later
