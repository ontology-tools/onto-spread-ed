# OSE Plugin: Annotation Sheets

OntoSpreadEd plugin for generating annotation sheet templates during ontology releases.

## Description

This plugin adds a release step that generates multi-sheet Excel workbooks for annotating research papers using ontology terms. Each sheet contains a hierarchical view of an ontology module with configurable annotation columns (e.g., "Entity present", "Evidence") grouped by arms (e.g., "Intervention", "Comparator").

## Installation

```bash
pip install ose-plugin-annotation-sheets
```

## Requirements

- Python 3.12+
- ose-core

## Usage

Add the `ANNOTATION_SHEETS` step to your `release_script.json`:

```json
{
  "name": "ANNOTATION_SHEETS",
  "args": {
    "included_files": ["module_a", "module_b"],
    "title": "My Ontology data extraction template",
    "arms": ["Intervention", "Comparator"],
    "annotation_columns": ["Entity present", "Evidence"]
  }
}
```

## License

LGPL-3.0-or-later
