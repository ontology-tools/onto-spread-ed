# OSE Core

Core library for OntoSpreadEd - Ontology Spreadsheet Editor.

## Description

This package contains the business logic, data models, and services for the OntoSpreadEd ontology spreadsheet editor. It provides:

- Data models for ontology entities (classes, properties, individuals)
- Database schema and migrations (using Alembic)
- Full-text search index (using Whoosh)
- Ontology processing and validation
- Release pipeline framework
- Plugin system infrastructure

## Installation

```bash
pip install ose-core
```

## Requirements

- Python 3.12+

## Dependencies

Key dependencies include:
- `py-horned-owl` - OWL ontology processing
- `pandas` / `openpyxl` - Excel file handling
- `whoosh` - Full-text search
- `SQLAlchemy` - Database ORM

## License

LGPL-3.0-or-later
