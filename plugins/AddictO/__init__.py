from ose.model.Plugin import Plugin
from .AddictOVocabReleaseStep import AddictOVocabReleaseStep



ADDICTO_PLUGIN = Plugin(
    id="org.bssofoundry.addicto",
    name="AddictO Plugin",
    version="0.1.0",
    description="Plugin for AddictO services and workflows.",
    contents=[
      AddictOVocabReleaseStep,
    ],
)
