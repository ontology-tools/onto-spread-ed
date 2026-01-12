from ose.model.Plugin import Plugin
from .GenerateHierarchicalSpreadsheetReleaseStep import GenerateHierarchicalSpreadsheetReleaseStep



HIERARCHICAL_SPREADSHEETS_PLUGIN = Plugin(
    id="org.bssofoundry.hierarchicalspreadsheets",
    name="HierarchicalSpreadsheet Plugin",
    version="0.1.0",
    description="Plugin to generate hierarchical spreadsheets during release.",
    contents=[
      GenerateHierarchicalSpreadsheetReleaseStep,
    ],
)