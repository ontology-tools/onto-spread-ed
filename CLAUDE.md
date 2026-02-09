# CLAUDE.md - Project Context for AI Assistants

## Project Overview

**OntoSpreadEd** (Ontology Spreadsheet Editor) is a Python/TypeScript monorepo for collaborative editing of OWL ontologies through spreadsheet interfaces. It enables domain experts to work with complex ontologies using familiar Excel-like views without requiring deep OWL syntax knowledge.

## Repository Structure

```
onto-spread-ed/
├── packages/                    # Core packages
│   ├── ose-core/               # Python: Business logic, models, services
│   ├── ose-app/                # Python: Flask web application
│   ├── ose-cli/                # Python: Command-line interface
│   ├── ose-js-core/            # TypeScript: Shared types and utilities
│   └── ose-js-app/             # TypeScript/Vue: Web UI components
├── plugins/                     # Plugin packages
│   ├── ose-plugin-addicto/     # AddictO ontology plugin
│   ├── ose-plugin-bcio/        # BCIO ontology plugin
│   ├── ose-plugin-hbcp/        # HBCP common services
│   └── ose-plugin-hierarchical-spreadsheets/  # Hierarchical export plugin
├── scripts/                     # Deployment and utility scripts
└── .github/workflows/          # CI/CD pipelines
```

## Technology Stack

- **Python 3.12+**: Flask, SQLAlchemy, py-horned-owl, Whoosh, pandas
- **TypeScript/Vue 3**: Vite, Bootstrap, Tabulator.js, D3.js
- **Build Tools**: uv (Python), npm workspaces (JS), Make
- **Linting**: ruff (Python), vue-tsc (TypeScript)

## Common Commands

### Installation
```bash
make install          # Install all dependencies (JS + Python)
make install-js       # Install npm dependencies only
make install-python   # Install Python packages with uv
```

### Building
```bash
make build            # Build everything (JS, CSS, Python)
make build-js         # Build TypeScript/Vue packages
make build-css        # Build SCSS to CSS
make build-python     # Build Python wheel packages
```

### Development
```bash
make dev              # Watch and rebuild JS on changes
make dev-python       # Run Flask dev server (flask --app ose_app:create_app run --debug)
```

### Linting & Testing
```bash
make lint             # Run Python linting (ruff)
make lint-python      # Run ruff check on packages/ and plugins/
make lint-python-fix  # Auto-fix Python linting issues
make type-check       # Run mypy type checking
make test             # Run pytest
```

### Cleaning
```bash
make clean            # Clean build artifacts
make clean-all        # Deep clean (includes node_modules, .venv)
```

## Package Dependencies

```
ose-core ─────────────────┬──────────────────────────────┐
    │                     │                              │
    ▼                     ▼                              ▼
ose-cli              ose-app                    ose-plugin-hbcp
                          │                              │
                          │                     ┌────────┴────────┐
                          │                     ▼                 ▼
                          │           ose-plugin-addicto  ose-plugin-bcio
                          │
                          ▼
              ose-plugin-hierarchical-spreadsheets

ose-js-core ──────► ose-js-app
```

## Plugin System

Plugins use Python entry points for discovery:

```toml
# In plugin's pyproject.toml
[project.entry-points.'ose.plugins']
my_plugin = "my_package:MY_PLUGIN"
```

Plugins can provide:
- **ReleaseStep** subclasses for ontology release pipelines
- **Script** subclasses for custom automation
- **Vue components** for UI customization (via `js_module` and `static_folder`)

## Key Directories

### Python Packages
- `packages/ose-core/src/ose/` - Core library
  - `model/` - Data models (Term, Relation, Plugin, etc.)
  - `services/` - Business services (PluginService, etc.)
  - `database/` - SQLAlchemy models and migrations
  - `release/` - Release pipeline framework
  - `index/` - Whoosh search indexing
- `packages/ose-app/src/ose_app/` - Flask application
  - `routes/` - API endpoints
  - `templates/` - Jinja2 templates
  - `static/` - Built JS/CSS assets (output from build)

### TypeScript Packages
- `packages/ose-js-core/src/` - Shared TypeScript utilities
- `packages/ose-js-app/src/` - Vue.js application
  - `editor/` - Spreadsheet editor components
  - `release/` - Release management UI
  - `visualise/` - Ontology visualization
  - `common/` - Shared Vue components

## Configuration Files

- `pyproject.toml` - Python workspace configuration (uv)
- `package.json` - npm workspace configuration
- `ruff.toml` - Python linting rules
- `tsconfig.json` - TypeScript configuration (in each package)
- `vite.config.ts` - Vite build configuration (in JS packages)

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/CI.yaml`) handles:
- **PR checks**: Python linting (ruff) and TypeScript type-checking (vue-tsc)
- **Build**: JS/CSS/Python package builds
- **Publish**: PyPI (ose-core, ose-app, ose-cli) and npm (@ontospreaded/js-core) on release
- **Deploy**: Automatic deployment to dev/prod environments

## Code Style

### Python
- Line length: 120 characters
- Linter: ruff with rules E4, E7, E9, F
- Target: Python 3.12

### TypeScript/Vue
- Strict mode enabled
- No unused locals/parameters
- Vue single-file components (.vue)

## Important Notes

1. **Build Order**: JS must be built before Python packages (static assets are included in wheels)
2. **Workspace Dependencies**: Use `workspace = true` in `[tool.uv.sources]` for local packages
3. **Plugin Static Assets**: Plugin JS/CSS goes in `src/<plugin_package>/static/`
4. **Database Migrations**: Run with `flask --app ose_app:create_app db upgrade`
