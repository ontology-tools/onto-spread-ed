# OntoSpreadEd Monorepo Makefile
# ================================
# Build system for all packages in the monorepo

.PHONY: all build build-js build-python build-plugins \
        install install-js install-python \
        dev dev-js dev-python \
        clean clean-js clean-python \
        test test-python lint \
        help

# ============================================================================
# Auto-detection of packages and plugins
# ============================================================================

# Find all Python packages (directories with pyproject.toml)
PYTHON_PACKAGES := $(shell find packages -maxdepth 2 -name "pyproject.toml" -exec dirname {} \;)
PYTHON_PLUGINS := $(shell find plugins -maxdepth 2 -name "pyproject.toml" -exec dirname {} \;)

RELEASE_PYTHON_PACKAGES := $(PYTHON_PACKAGES)
RELEASE_PYTHON_PLUGINS := ose-plugin-hierarchical-spreadsheets ose-plugin-annotation-sheets

# Find all JS packages (directories with package.json, excluding node_modules)
JS_PACKAGES := $(shell find packages -maxdepth 2 -name "package.json" ! -path "*/node_modules/*" -exec dirname {} \;)
JS_PLUGINS := $(shell find plugins -maxdepth 2 -name "package.json" ! -path "*/node_modules/*" -exec dirname {} \;)

RELEASE_JS_PACKAGES := $(JS_PACKAGES)
RELEASE_JS_PLUGINS := 

# Default target
all: install build

# ============================================================================
# Installation
# ============================================================================

## Install all dependencies (JS and Python)
install: install-js install-python

## Install JavaScript/TypeScript dependencies
install-js:
	npm install

## Install Python packages in editable mode with uv
install-python:
	uv sync --all-packages --all-groups

# ============================================================================
# Build
# ============================================================================

# Helper to extract package name from package.json
define get_pkg_name
$(shell node -p "require('$(1)/package.json').name")
endef

## Build everything (JS first, then Python packages which include static files)
build: build-js build-python

## Build all JavaScript/TypeScript packages and plugins
## Root `npm run build`: js-core -> shims -> js-app (CSS is bundled by vite), then plugins
build-js:
	npm run build
	@for plugin in $(JS_PLUGINS); do \
		pkg_name=$$(node -p "require('./$$plugin/package.json').name"); \
		echo "Building JS plugin: $$pkg_name"; \
		npm -w "$$pkg_name" run build || true; \
	done

## Build Python packages
build-python: build-js
	@for pkg in $(PYTHON_PACKAGES) $(PYTHON_PLUGINS); do \
		echo "Building Python package: $$pkg"; \
		uv build --package $$(basename $$pkg); \
	done

# ============================================================================
# Development (watch mode)
# ============================================================================

## Start development mode: vite serve on :5173 (proxies to Flask on :5000) plus Flask
dev:
	@echo ">>> Open http://localhost:5173 (vite dev server, proxies the API to Flask on :5000)"
	$(MAKE) -j2 dev-js dev-python

## Run the vite dev server on :5173 (generates the shims first)
dev-js:
	npm run dev

## Run the Flask development server
dev-python:
	uv run flask --app ose_app:create_app run --debug --port 5000

# ============================================================================
# Database
# ============================================================================

## Run database migrations
db-upgrade:
	flask --app ose_app:create_app db upgrade

## Create a new database migration
db-migrate:
	flask --app ose_app:create_app db migrate

# ============================================================================
# Testing & Linting
# ============================================================================

## Run all tests
test: test-python

## Run Python tests
test-python:
	pytest

## Run linting
lint: lint-python

## Run Python linting with ruff
lint-python:
	uv run ruff check packages/ plugins/

## Fix Python linting issues
lint-python-fix:
	uv run ruff check --fix packages/ plugins/
## Run type checking
type-check:
	uv run mypy packages/
	uv run mypy plugins/

# ============================================================================
# Cleaning
# ============================================================================

## Clean all build artifacts
clean: clean-js clean-python

## Clean JavaScript build artifacts
clean-js:
	@for pkg in $(JS_PACKAGES); do \
		pkg_name=$$(node -p "require('./$$pkg/package.json').name"); \
		npm -w "$$pkg_name" run clean 2>/dev/null || true; \
	done
	@for plugin in $(JS_PLUGINS); do \
		pkg_name=$$(node -p "require('./$$plugin/package.json').name"); \
		npm -w "$$pkg_name" run clean 2>/dev/null || true; \
	done

## Clean Python build artifacts
clean-python:
	rm -rf dist build *.egg-info
	@for dir in $(PYTHON_PACKAGES) $(PYTHON_PLUGINS); do \
		find $$dir -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "build" -exec rm -rf {} + 2>/dev/null || true; \
		find $$dir -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true; \
	done

## Deep clean (including node_modules and .venv)
clean-all: clean
	rm -rf node_modules
	rm -rf .venv
	find packages plugins -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true

# ============================================================================
# Release
# ============================================================================

## Build for production
build-prod: clean build
	@echo "Removing packages not meant for publishing."
	find dist -mindepth 1 -and -name "ose*" -and -not \(\
		-name "ose_app*" \
		-o -name "ose_cli*" \
		-o -name "ose_core*" \
		-o -name "ose_plugin_hierarchical_spreadsheets*" \
		-o -name "ose_plugin_annotation_sheets*" \
	\) -exec rm -rf {} + 

# ============================================================================
# Help
# ============================================================================

## Show this help message
help:
	@echo "OntoSpreadEd Monorepo Build System"
	@echo "==================================="
	@echo ""
	@echo "Detected packages:"
	@echo "  Python: $(PYTHON_PACKAGES) $(PYTHON_PLUGINS)"
	@echo "  JS:     $(JS_PACKAGES) $(JS_PLUGINS)"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Main targets:"
	@echo "  all              - Install dependencies and build everything (default)"
	@echo "  install          - Install all dependencies"
	@echo "  build            - Build all packages"
	@echo "  dev              - Start vite serve (:5173) and Flask (:5000); open http://localhost:5173"
	@echo "  test             - Run all tests"
	@echo "  lint             - Run linting"
	@echo "  clean            - Clean build artifacts"
	@echo "  help             - Show this help message"
	@echo ""
	@echo "JavaScript targets:"
	@echo "  install-js       - Install npm dependencies"
	@echo "  build-js         - Build all JS/TS packages (auto-detected)"
	@echo "  dev-js           - Run the vite dev server on :5173"
	@echo "  clean-js         - Clean JS build artifacts"
	@echo ""
	@echo "Python targets:"
	@echo "  install-python   - Install Python packages (uv)"
	@echo "  build-python     - Build all Python packages"
	@echo "  dev-python       - Run Flask dev server"
	@echo "  test-python      - Run Python tests"
	@echo "  lint-python      - Run ruff linting"
	@echo "  lint-python-fix  - Fix ruff linting issues"
	@echo "  type-check       - Run mypy type checking"
	@echo "  clean-python     - Clean Python build artifacts"
	@echo ""
	@echo "Database targets:"
	@echo "  db-upgrade       - Run database migrations"
	@echo "  db-migrate       - Create a new migration"
	@echo ""
	@echo "Other targets:"
	@echo "  build-prod       - Clean and build for production"
	@echo "  clean-all        - Deep clean (includes node_modules, .venv)"
