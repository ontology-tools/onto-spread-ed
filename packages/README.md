# OntoSpreadEd Monorepo Packages

This directory contains the monorepo packages for OntoSpreadEd.

## Package Overview

| Package | Type | Description | PyPI/npm Name |
|---------|------|-------------|---------------|
| `ose-lib` | Python | Core library (project config, ontology building) | `ose-lib` |
| `ose-cli` | Python | CLI commands (depends on ose-lib) | `ose-cli` |
| `ose-app` | Python | Flask backend: JSON API, OAuth, serves the SPA (depends on ose-lib) | `ose-app` |
| `ose-js-core` | TypeScript | Shared types, models, utilities | `@ontospreaded/js-core` |
| `ose-js-app` | TypeScript/Vue | Vue single-page web app | (internal) |

## Directory Structure

```
packages/
├── ose-lib/            # Python core library
│   ├── src/ose/
│   │   ├── project.py  # Project (repository) configuration
│   │   ├── building/   # Ontology build stages
│   │   ├── ontology/
│   │   ├── schema/
│   │   └── utils/      # Utility functions
│   └── pyproject.toml
│
├── ose-cli/            # Python CLI package
│   ├── src/ose_cli/
│   │   ├── main.py     # CLI entry point
│   │   ├── release.py  # Release commands
│   │   └── externals.py
│   └── pyproject.toml
│
├── ose-app/            # Flask web application
│   ├── src/ose_app/
│   │   ├── routes/     # api/ (JSON API), auth.py, status.py, spa.py (SPA catch-all)
│   │   ├── database/   # SQLAlchemy models
│   │   ├── guards/     # Auth decorators
│   │   └── static/app/ # Built Vue SPA (output of the ose-js-app build)
│   ├── API.md          # JSON API reference
│   └── pyproject.toml
│
├── ose-js-core/        # Shared TypeScript library
│   ├── src/
│   │   ├── model.ts    # TypeScript types/interfaces
│   │   ├── types.ts
│   │   └── utils/
│   ├── package.json
│   └── tsconfig.json
│
└── ose-js-app/         # Vue single-page app
    ├── index.html      # SPA entry
    ├── public/         # Generated plugin shims (vue-shim.js, ose-js-core-shim.js)
    ├── src/
    │   ├── main.ts, App.vue, router.ts, api.ts, config.ts, state.ts
    │   ├── pages/      # Home, Repo browser, Forbidden, LoggedOut, NotFound
    │   ├── admin/      # Admin dashboard, index rebuild
    │   ├── editor/     # Spreadsheet editor
    │   ├── release/    # Release management UI
    │   ├── settings/   # Settings UI
    │   ├── visualise/  # Graph visualization (popup)
    │   └── common/     # Shared Vue components
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

## Installation

### Python Packages (Development)

```bash
# Install all packages in editable mode
pip install -e packages/ose-lib -e packages/ose-cli -e packages/ose-app

# Or with uv
uv pip install -e packages/ose-lib -e packages/ose-cli -e packages/ose-app
```

### Python Packages (Production)

```bash
# Install only the CLI
pip install ose-cli

# Install the full web application
pip install ose-app
```

### JavaScript Packages

```bash
# Using npm workspaces
npm install

# Build all JS packages: js-core -> shims -> js-app (-> ose-app/src/ose_app/static/app)
npm run build

# Or using pnpm
pnpm install
pnpm build
```

## Development

### Running the Flask App

```bash
make dev-python   # Flask on :5000
make dev          # Flask on :5000 plus vite serve on :5173
```

Open the app at `http://localhost:5173`; the vite dev server proxies the API and login routes to Flask on :5000.

### Building JavaScript

```bash
# Build JS core library
npm run build:js-core

# Generate the plugin shims (needs js-core built)
npm run build:shims

# Build Vue app
npm run build:js-app

# Dev server on :5173 (generates shims, then vite serve; needs Flask running)
npm run dev

# Old flow: vite build --watch into Flask's static folder (open :5000)
npm -w @ontospreaded/js-app run watch
```

### Using the CLI

```bash
# After installing ose-cli
ose --help
```

## Dependencies

```
ose-cli ──depends──> ose-lib
ose-app ──depends──> ose-lib

@ontospreaded/js-app ──depends──> @ontospreaded/js-core
```
