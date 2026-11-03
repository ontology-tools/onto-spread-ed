# OSE Plugin: Hierarchical Spreadsheets

OntoSpreadEd plugin for generating hierarchical spreadsheet exports during ontology releases.

## Description

This plugin adds a build stage that generates hierarchical spreadsheet representations of ontologies. It exports ontology structures in a format that preserves parent-child relationships in an easy-to-read tabular format.

## Installation

```bash
pip install ose-plugin-hierarchical-spreadsheets
```

## Requirements

- Python 3.13+
- ose-lib

## Usage

Add the `HIERARCHICAL_SPREADSHEETS` to your release script configuration to include hierarchical spreadsheet generation in your release pipeline.

## License

LGPL-3.0-or-later

## Discovery

The `ose.build_stages` group exposes `HIERARCHICAL_SPREADSHEETS` to the app and standalone CLI.
Arguments stay in the stage’s `args` mapping; inputs are read from the build directory.
