# OSE Plugin: HBCP

OntoSpreadEd plugin for HBCP (Human Behaviour Change Project) services.

## Description

This plugin provides common functionality for HBCP-related ontology projects. It serves as a shared library with shared services used by plugins like AddictO and BCIO.

Features:
- Search API client for external vocabulary services
- HTTP error handling utilities
- Common service infrastructure

## Installation

```bash
pip install ose-plugin-hbcp
```

## Requirements

- Python 3.13+
- ose-lib

## License

LGPL-3.0-or-later

HBCP registers no entry points. `APIService` takes a `dict[str, str]` of prefixes,
independent of Flask configuration. Runtime dependencies include `aiohttp` and `async-lru`.
