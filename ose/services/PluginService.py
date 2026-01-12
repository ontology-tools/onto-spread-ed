import logging
import os
from typing import Type

from injector import Injector, inject
from ose.model.Script import Script
from ose.release.ReleaseStep import ReleaseStep
from ose.services.ConfigurationService import ConfigurationService
from ose.model.Plugin import Plugin, PLUGIN_CONTENT

PROP_PLUGINS_DIRECTORY = "PLUGINS_DIRECTORY"


def dir_is_py_module(path: str) -> bool:
    return os.path.isdir(path) and os.path.exists(os.path.join(path, "__init__.py"))


class PluginService:
    _logger = logging.getLogger(__name__)

    def __init__(self, config: ConfigurationService, injector: Injector):
        self._plugins: list[Plugin] = []
        self._config = config
        self._injector = injector

    @property
    def plugins(self) -> list[Plugin]:
        return self._plugins

    def get_release_steps(self) -> list[Type[ReleaseStep]]:
        return [c for plugin in self._plugins for c in plugin.contents if issubclass(c, ReleaseStep)]

    def get_scripts(self) -> list[Script]:
        return [self._injector.create_object(c) for plugin in self._plugins for c in plugin.contents if issubclass(c, Script)]

    def load_plugins(self):
        plugins_dir = os.path.abspath(self._config.app_config.get(PROP_PLUGINS_DIRECTORY, "plugins"))

        plugin_modules = [
            os.path.abspath(os.path.join(plugins_dir, p))
            for p in os.listdir(plugins_dir)
            if dir_is_py_module(os.path.join(plugins_dir, p))
        ]

        self._logger.debug(f"Found plugin modules: {[plugin_modules]}")

        for module_path in plugin_modules:
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "plugins." + os.path.basename(module_path), os.path.join(module_path, "__init__.py")
            )

            if spec is None or spec.loader is None:
                self._logger.warning(f"Could not load plugin module from path: {module_path}")
                continue

            plugin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin_module)

            plugin = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if isinstance(attr, Plugin):
                    if plugin is None:
                        plugin = attr
                    else:
                        self._logger.warning(
                            f"Multiple Plugin instances found in module: {module_path}. Aborting loading this module."
                        )

            if plugin is not None:
                self._plugins.append(plugin)
                self._logger.info(f"Loaded plugin: {plugin.name} (version: {plugin.version})")
            else:
                self._logger.warning(f"No Plugin instance found in module: {module_path}.")
