from ose.model.Plugin import Plugin, PluginComponent
from .AddictOVocabReleaseStep import AddictOVocabReleaseStep


AddictOPlugin = Plugin(
    id="org.bssofoundry.addicto",
    name="AddictO Plugin",
    version="0.1.0",
    description="Plugin for AddictO services and workflows.",
    contents=[
        AddictOVocabReleaseStep,
    ],
    components=[
        PluginComponent(
            step_name="ADDICTO_VOCAB",
            component_name="AddictOVocab",
        ),
    ],
    js_module="ose-plugin-addicto.js",
)
