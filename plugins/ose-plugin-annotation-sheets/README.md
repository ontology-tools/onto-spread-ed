# OSE Plugin: Annotation Sheets

OntoSpreadEd plugin for generating annotation sheet templates during ontology releases.

## Description

This plugin adds a build stage that generates multi-sheet Excel workbooks for annotating research papers using ontology terms. Each sheet contains a hierarchical view of an ontology module with configurable annotation columns (e.g., "Entity present", "Evidence") grouped by arms (e.g., "Intervention", "Comparator").

## Installation

```bash
pip install ose-plugin-annotation-sheets
```

## Requirements

- Python 3.13+
- ose-lib

## Usage

Add the `ANNOTATION_SHEETS` step to your `project build configuration`:

```json
{
  "name": "ANNOTATION_SHEETS",
  "args": {
    "included_files": ["module_a", "module_b"],
    "arms": ["Intervention", "Comparator"],
    "annotation_columns": ["Entity present", "Evidence"]
  }
}
```

## License

LGPL-3.0-or-later

## Discovery

The `ose.build_stages` group exposes `ANNOTATION_SHEETS` to the app and standalone CLI.
Arguments stay in the stage’s `args` mapping; inputs are read from the build directory.
`intro_sheet`, when provided, must already exist in the build directory. Other arguments
include `sheets`, `arms`, `annotation_columns`, `article_header` and `output_filename`.
