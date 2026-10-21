from dataclasses import dataclass, field
from typing import Type

from ose_app.model.Script import Script


@dataclass
class PluginComponent:
    step_name: str
    component_name: str


@dataclass
class Plugin:
    id: str
    name: str
    version: str
    description: str
    contents: list[Type[Script]] = field(default_factory=list)
    components: list[PluginComponent] = field(default_factory=list)
    static_folder: str | None = None
    """Defaults to 'static' in the plugin package."""
    js_module: str | None = None
    """Module in static_folder that exports the Vue components."""
