"""
Lightweight plugin discovery for release steps.

Discovers ReleaseStep subclasses from installed plugins via entry_points,
without requiring ConfigurationService, Injector, or Flask.
"""

import logging
from importlib.metadata import entry_points
from typing import Dict, Type

from .ReleaseStep import ReleaseStep
from ..model.Plugin import Plugin

logger = logging.getLogger(__name__)

PLUGIN_ENTRY_POINT_GROUP = "ose.plugins"


def discover_plugin_release_steps() -> Dict[str, Type[ReleaseStep]]:
    """
    Discover ReleaseStep subclasses from installed plugins.

    Scans entry points in the 'ose.plugins' group and extracts any
    ReleaseStep subclasses from the plugin contents.

    :return: A dictionary mapping step names to step classes.
    """
    steps: Dict[str, Type[ReleaseStep]] = {}

    eps = entry_points(group=PLUGIN_ENTRY_POINT_GROUP)
    logger.debug(f"Found {len(eps)} plugin entry points")

    for ep in eps:
        try:
            plugin = ep.load()

            if not isinstance(plugin, Plugin):
                logger.debug(
                    f"Entry point '{ep.name}' did not return a Plugin instance, skipping"
                )
                continue

            for content_type in plugin.contents:
                if isinstance(content_type, type) and issubclass(content_type, ReleaseStep):
                    steps[content_type.name()] = content_type
                    logger.debug(f"Discovered plugin release step: {content_type.name()}")

            logger.debug(f"Loaded plugin: {plugin.name} (version: {plugin.version})")

        except Exception as e:
            logger.warning(f"Failed to load plugin from entry point '{ep.name}': {e}")

    return steps
