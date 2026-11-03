import inspect
import logging
from dataclasses import asdict, dataclass
from importlib import import_module
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from types import ModuleType

from injector import Injector
from flask import url_for

from ose.building.stages import BuildStage
from ose_app.model import WebPlugin
from ose_app.model.Script import Script


@dataclass(frozen=True)
class _PluginInfo:
    id: str
    type: str
    distribution: str | None
    version: str | None

    @classmethod
    def from_entry_point(cls, ep: EntryPoint, group: str) -> "_PluginInfo":
        return cls(
            id=ep.name,
            type=group,
            distribution=ep.dist.metadata["Name"] if ep.dist else None,
            version=ep.dist.version if ep.dist else None,
        )


@dataclass(frozen=True)
class _DiscoveredWebPlugin:
    plugin: WebPlugin
    static_path: Path


class PluginService:
    _logger = logging.getLogger(__name__)

    def __init__(self, injector: Injector):
        self._injector = injector
        self._scripts: list[type[Script]] = []
        self._web_plugins: dict[str, _DiscoveredWebPlugin] = {}
        self._plugin_info: dict[str, list[_PluginInfo]] = {}

    def discover_all(self) -> None:
        self.discover_build_stages()
        self.discover_scripts()
        self.discover_web_plugins()

    def _discover_classes[T](self, group: str, base: type[T]) -> list[type[T]]:
        classes = []
        self._plugin_info[group] = []
        for ep in sorted(entry_points(group=group), key=lambda ep: ep.name):
            try:
                module = ep.load()
                if not isinstance(module, ModuleType):
                    raise TypeError("Expected a module")
                discovered = [
                    cls for _, cls in inspect.getmembers(module, inspect.isclass)
                    if issubclass(cls, base) and not inspect.isabstract(cls)
                ]
                classes.extend(discovered)
                self._plugin_info[group].append(_PluginInfo.from_entry_point(ep, group))
            except Exception:
                self._logger.exception("Failed to load '%s' from %s", ep.name, group)
        return classes

    def discover_scripts(self):
        self._scripts = self._discover_classes("ose.scripts", Script)
        self._logger.info("Discovered %d scripts", len(self._scripts))

    def discover_build_stages(self):
        """Record stage plugins for the overview; builds discover stages through ose-lib."""
        stages = self._discover_classes("ose.build_stages", BuildStage)
        self._logger.info("Discovered %d plugin build stages", len(stages))

    def discover_web_plugins(self):
        group = "ose.web_plugins"
        self._web_plugins = {}
        self._plugin_info[group] = []
        for ep in sorted(entry_points(group=group), key=lambda ep: ep.name):
            try:
                plugin = ep.load()
                if not isinstance(plugin, WebPlugin):
                    raise TypeError("Expected a WebPlugin instance")
                module = import_module(ep.module)
                static = Path(module.__file__).parent / plugin.static_folder
                info = _PluginInfo.from_entry_point(ep, group)
                self._web_plugins[ep.name] = _DiscoveredWebPlugin(plugin=plugin, static_path=static)
                self._plugin_info[group].append(info)
            except Exception:
                self._logger.exception("Failed to load web plugin '%s'", ep.name)

        self._logger.info("Discovered %d web plugins", len(self._web_plugins))

    def get_scripts(self) -> list[Script]:
        return [self._injector.create_object(cls) for cls in self._scripts]

    def get_plugin_static_path(self, plugin_id: str) -> Path | None:
        plugin = self._web_plugins.get(plugin_id)
        return plugin.static_path if plugin is not None else None

    def get_plugins_info(self) -> list[dict]:
        result = []
        plugins = (plugin for group in self._plugin_info.values() for plugin in group)
        for info in sorted(plugins, key=lambda plugin: (plugin.id, plugin.type)):
            item = asdict(info)
            if info.type == "ose.web_plugins":
                item["module_url"] = url_for(
                    "api_plugins.get_plugin_static",
                    plugin_id=info.id,
                    filename=self._web_plugins[info.id].plugin.module,
                )
            result.append(item)
        return result
