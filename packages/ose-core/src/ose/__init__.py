"""
OSE Core - Core library for OntoSpreadEd

This package contains the business logic, models, and services
for the OntoSpreadEd ontology spreadsheet editor.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-core")
except PackageNotFoundError:
    __version__ = "unknown"

# Re-export commonly used classes
from .model import *  # noqa: F401, F403
