from dataclasses import dataclass
from typing import Type, TypeGuard

from ose.model.Script import Script
from ose.release.ReleaseStep import ReleaseStep

PLUGIN_CONTENT = Script | ReleaseStep


@dataclass
class Plugin:
    id: str
    name: str
    version: str
    description: str
    contents: list[Type[PLUGIN_CONTENT]]
    

