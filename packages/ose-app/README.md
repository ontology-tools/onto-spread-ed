# OSE App

Flask web application for OntoSpreadEd - Ontology Spreadsheet Editor.

## Description

This package provides the web interface and REST API for the OntoSpreadEd ontology spreadsheet editor. It includes:

- Flask application factory and configuration
- JSON API endpoints for ontology operations (see [API.md](API.md))
- Serving the Vue single-page app (`ose-js-app`) as a catch-all
- GitHub OAuth authentication
- User and permission management
- Caching of files from GitHub
- Running releases (builds) of the ontologies

## Installation

```bash
pip install ose-app
```

For development with CLI tools:
```bash
pip install ose-app[cli]
```

## Requirements

- Python 3.13+

## Configuration

The application is configured via `config.yaml` or environment variables. See the main project [README](https://github.com/ontology-tools/onto-spread-ed/blob/main/README.md) for configuration options.

The release runner uses these app settings (all timing values are in seconds):

| Setting | Default | Purpose |
| --- | --- | --- |
| `RELEASE_MAX_PARALLEL` | `2` | Maximum releases executing at once |
| `RELEASE_POLL_INTERVAL` | `2.0` | Time between request polls |
| `RELEASE_HEARTBEAT_INTERVAL` | `10.0` | Time between heartbeat updates and stale-runner checks |
| `RELEASE_LEASE_TIMEOUT` | `60.0` | Time without a heartbeat before takeover; keep longer than the heartbeat interval |
| `RELEASE_PROGRESS_INTERVAL` | `1.0` | Minimum time between progress writes; `0` disables throttling |

## Usage

```bash
flask --app ose_app:create_app run
```

## License

LGPL-3.0-or-later
