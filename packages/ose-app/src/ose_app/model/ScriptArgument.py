from dataclasses import dataclass
from typing import Literal


@dataclass
class ScriptArgument:
    name: str
    description: str
    type: Literal["string", "integer", "boolean", "float"] = "string"
    default: str | None = None