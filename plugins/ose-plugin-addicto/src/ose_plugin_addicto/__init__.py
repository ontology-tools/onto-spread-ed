from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-plugin-addicto")
except PackageNotFoundError:
    __version__ = "unknown"
