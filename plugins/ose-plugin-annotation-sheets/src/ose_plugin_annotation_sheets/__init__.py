from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-plugin-annotation-sheets")
except PackageNotFoundError:
    __version__ = "unknown"
