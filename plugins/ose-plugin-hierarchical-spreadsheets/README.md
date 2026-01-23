# OSE Plugin: Hierarchical Spreadsheets

OntoSpreadEd plugin for generating hierarchical spreadsheet exports during ontology releases.

## Description

This plugin adds a release step that generates hierarchical spreadsheet representations of ontologies. It exports ontology structures in a format that preserves parent-child relationships in an easy-to-read tabular format.

## Installation

```bash
pip install ose-plugin-hierarchical-spreadsheets
```

## Requirements

- Python 3.12+
- ose-core

## Usage

Add the `GenerateHierarchicalSpreadsheetReleaseStep` to your release script configuration to include hierarchical spreadsheet generation in your release pipeline.

## License

LGPL-3.0-or-later
