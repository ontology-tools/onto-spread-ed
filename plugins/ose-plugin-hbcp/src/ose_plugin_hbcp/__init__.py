"""Shared search API support for ontology plugins."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ose-plugin-hbcp")
except PackageNotFoundError:
    __version__ = "unknown"
