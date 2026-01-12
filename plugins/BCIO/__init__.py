from ose.model.Plugin import Plugin
from .BCIOSearchReleaseStep import BCIOSearchReleaseStep
from ..HierarchicalSpreadSheets.GenerateHierarchicalSpreadsheetReleaseStep import GenerateHierarchicalSpreadsheetReleaseStep
from .scripts.cleanup_bcio_vocab import CleanUpBCIOVocabScript
from .scripts.import_missing_externals import ImportMissingExternalsScript
from .scripts.update_imports_to_latest_versions import UpdateImportsToLatestVersionsScript
from .scripts.set_pre_proposed_curation_status import SetPreProposedCurationStatusScript



BCIO_PLUGIN = Plugin(
    id="org.bssofoundry.bcio",
    name="BCIO Plugin",
    version="0.1.0",
    description="Plugin for BCIO services and workflows.",
    contents=[
      BCIOSearchReleaseStep,
      GenerateHierarchicalSpreadsheetReleaseStep,
      CleanUpBCIOVocabScript,
      ImportMissingExternalsScript,
      UpdateImportsToLatestVersionsScript,
      SetPreProposedCurationStatusScript,
    ],
)
