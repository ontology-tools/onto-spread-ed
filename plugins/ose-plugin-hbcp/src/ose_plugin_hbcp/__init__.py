from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-plugin-hbcp")
except PackageNotFoundError:
    __version__ = "unknown"

from ose.model.Plugin import Plugin


HBCPPlugin = Plugin(
    id="org.bssofoundry.hbcp",
    name="HBCP Plugin",
    version="0.1.0",
    description="Plugin for HBCP services and workflows. Provides common functionality for derived plugins.",
    contents=[],
    components=[],
)
