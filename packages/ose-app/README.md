# OSE App

Flask web application for OntoSpreadEd - Ontology Spreadsheet Editor.

## Description

This package provides the web interface and REST API for the OntoSpreadEd ontology spreadsheet editor. It includes:

- Flask application factory and configuration
- REST API endpoints for ontology operations
- GitHub OAuth authentication
- User and permission management
- Ontology data store and caching

## Installation

```bash
pip install ose-app
```

For development with CLI tools:
```bash
pip install ose-app[cli]
```

## Requirements

- Python 3.12+

## Configuration

The application is configured via `config.yaml` or environment variables. See the main project [README](https://github.com/ontology-tools/onto-spread-ed/blob/main/README.md) for configuration options.

## Usage

```bash
flask --app ose_app:create_app run
```

## License

LGPL-3.0-or-later
