from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-plugin-hierarchical-spreadsheets")
except PackageNotFoundError:
    __version__ = "unknown"
