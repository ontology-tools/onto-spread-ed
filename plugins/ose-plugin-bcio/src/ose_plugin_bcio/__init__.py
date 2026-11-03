from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-plugin-bcio")
except PackageNotFoundError:
    __version__ = "unknown"
