from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ose-plugin-annotation-sheets")
except PackageNotFoundError:
    __version__ = "unknown"

from ose.model.Plugin import Plugin
from .GenerateAnnotationSheetsReleaseStep import GenerateAnnotationSheetsReleaseStep


AnnotationSheetsPlugin = Plugin(
    id="org.bssofoundry.annotationsheets",
    name="Annotation Sheets Plugin",
    version="0.1.0",
    description="Plugin to generate annotation sheet templates during release.",
    contents=[
        GenerateAnnotationSheetsReleaseStep,
    ],
)
