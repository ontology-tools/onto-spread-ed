from dataclasses import dataclass


@dataclass(frozen=True)
class WebPlugin:
    module: str
    static_folder: str = "static"
