# OntoSpreadEd Monorepo Packages

This directory contains the monorepo packages for OntoSpreadEd.

## Package Overview

| Package | Type | Description | PyPI/npm Name |
|---------|------|-------------|---------------|
| `ose-core` | Python | Core business logic, models, services | `ose-core` |
| `ose-cli` | Python | CLI commands (depends on ose-core) | `ose-cli` |
| `ose-app` | Python | Flask web application (depends on ose-core) | `ose-app` |
| `ose-js-core` | TypeScript | Shared types, models, utilities | `@ose/js-core` |
| `ose-js-app` | TypeScript/Vue | Vue.js web app components | (internal) |

## Directory Structure

```
packages/
├── ose-core/           # Python core library
│   ├── src/ose_core/
│   │   ├── model/      # Data models (Term, ExcelOntology, etc.)
│   │   ├── services/   # Business services
│   │   ├── release/    # Release logic
│   │   ├── index/      # Search indexing
│   │   ├── commands/   # Command implementations
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
│   │   ├── routes/     # Flask blueprints
│   │   ├── database/   # SQLAlchemy models
│   │   ├── guards/     # Auth decorators
│   │   ├── templates/  # Jinja2 templates
│   │   └── static/     # Static assets (compiled JS/CSS)
│   ├── migrations/     # Alembic database migrations
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
└── ose-js-app/         # Vue.js application
    ├── src/
    │   ├── admin/      # Admin dashboard
    │   ├── editor/     # Spreadsheet editor
    │   ├── release/    # Release management UI
    │   ├── settings/   # Settings UI
    │   ├── visualise/  # Graph visualization
    │   └── common/     # Shared Vue components
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

## Installation

### Python Packages (Development)

```bash
# Install all packages in editable mode
pip install -e packages/ose-core -e packages/ose-cli -e packages/ose-app

# Or with uv
uv pip install -e packages/ose-core -e packages/ose-cli -e packages/ose-app
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

# Build all JS packages
npm run build

# Or using pnpm
pnpm install
pnpm build
```

## Development

### Running the Flask App

```bash
cd packages/ose-app
flask run --debug
```

### Building JavaScript

```bash
# Build JS core library
npm -w @ose/js-core run build

# Build Vue app
npm -w @ose/js-app run build

# Watch mode
npm -w @ose/js-app run dev
```

### Using the CLI

```bash
# After installing ose-cli
ose --help
```

## Dependencies

```
ose-cli ──depends──> ose-core
ose-app ──depends──> ose-core

@ose/js-app ──depends──> @ose/js-core
```
