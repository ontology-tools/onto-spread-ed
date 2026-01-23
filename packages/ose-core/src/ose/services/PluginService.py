import logging
import importlib.resources
from importlib.metadata import entry_points
from pathlib import Path
from typing import Type

from injector import Injector
from ose.model.Script import Script
from ose.release.ReleaseStep import ReleaseStep
from ose.services.ConfigurationService import ConfigurationService
from ose.model.Plugin import Plugin, PluginComponent

PLUGIN_ENTRY_POINT_GROUP = "ose.plugins"


class PluginService:
    _logger = logging.getLogger(__name__)

    def __init__(self, config: ConfigurationService, injector: Injector):
        self._plugins: list[Plugin] = []
        self._plugin_packages: dict[str, str] = {}  # plugin_id -> package_name
        self._config = config
        self._injector = injector

    @property
    def plugins(self) -> list[Plugin]:
        return self._plugins

    def get_release_steps(self) -> list[Type[ReleaseStep]]:
        return [c for plugin in self._plugins for c in plugin.contents if issubclass(c, ReleaseStep)]

    def get_scripts(self) -> list[Script]:
        return [self._injector.create_object(c) for plugin in self._plugins for c in plugin.contents if issubclass(c, Script)]

    def get_plugin_components(self) -> dict[str, tuple[Plugin, PluginComponent]]:
        """Get all plugin components mapped by their step name."""
        return {
            comp.step_name: (plugin, comp)
            for plugin in self._plugins
            for comp in plugin.components
        }

    def get_plugin_static_path(self, plugin_id: str) -> Path | None:
        """Get the path to a plugin's static folder.
        
        Returns None if the plugin doesn't exist or has no static folder.
        """
        plugin = next((p for p in self._plugins if p.id == plugin_id), None)
        if plugin is None:
            return None

        package_name = self._plugin_packages.get(plugin_id)
        if package_name is None:
            return None

        try:
            static_folder = plugin.static_folder or "static"
            files = importlib.resources.files(package_name)
            static_path = files.joinpath(static_folder)

            # For traversable resources, get the actual filesystem path
            with importlib.resources.as_file(static_path) as path:
                # Return a copy of the path since the context manager may clean up
                return Path(path)
        except (TypeError, FileNotFoundError, OSError):
            return None

    def get_plugins_info(self) -> list[dict]:
        """Get serializable information about all loaded plugins for the frontend."""
        result = []
        for plugin in self._plugins:
            info = {
                "id": plugin.id,
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "components": [
                    {"step_name": c.step_name, "component_name": c.component_name}
                    for c in plugin.components
                ],
                "has_static": self.get_plugin_static_path(plugin.id) is not None,
                "js_module": plugin.js_module
            }
            result.append(info)
        return result

    def load_plugins(self):
        """Load plugins using Python's entry points system.
        
        Plugins should define entry points in the 'ose.plugins' group.
        Each entry point should point to a Plugin instance.
        
        Example in pyproject.toml:
            [project.entry-points.'ose.plugins']
            my_plugin = "my_package:MY_PLUGIN"
        """
        eps = entry_points(group=PLUGIN_ENTRY_POINT_GROUP)

        self._logger.debug(f"Found {len(eps)} plugin entry points")

        for ep in eps:
            try:
                plugin = ep.load()

                if not isinstance(plugin, Plugin):
                    self._logger.warning(
                        f"Entry point '{ep.name}' did not return a Plugin instance, got {type(plugin).__name__}"
                    )
                    continue

                self._plugins.append(plugin)
                # Store the package name for later use
                self._plugin_packages[plugin.id] = ep.value.split(":")[0]
                self._logger.info(f"Loaded plugin: {plugin.name} (version: {plugin.version})")

            except Exception as e:
                self._logger.error(f"Failed to load plugin from entry point '{ep.name}': {e}")

