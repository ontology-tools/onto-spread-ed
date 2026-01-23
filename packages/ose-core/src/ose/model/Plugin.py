from dataclasses import dataclass, field
from typing import Type

from ose.model.Script import Script
from ose.release.ReleaseStep import ReleaseStep

PLUGIN_CONTENT = Script | ReleaseStep


@dataclass
class PluginComponent:
    """A Vue component provided by a plugin for a specific release step."""
    step_name: str
    """The name of the release step this component handles (e.g., 'ADDICTO_VOCAB')."""
    component_name: str
    """The name of the Vue component to use (as exported from the plugin's JS module)."""


@dataclass
class Plugin:
    id: str
    name: str
    version: str
    description: str
    contents: list[Type[PLUGIN_CONTENT]] = field(default_factory=list)
    components: list[PluginComponent] = field(default_factory=list)
    """Vue components provided by this plugin for release steps."""
    static_folder: str | None = None
    """Path to the folder containing static assets (JS, CSS) for this plugin.
    If None, defaults to 'static' relative to the plugin's package."""
    js_module: str | None = None
    """The name of the JavaScript module file (e.g., 'my-plugin.js').
    This file should be in the static_folder and export the Vue components."""
    

