from importlib.metadata import entry_points
from typing import Type

PLUGIN_ENTRY_POINT_GROUP = "ose.plugins"


def for_type[T](typ: Type[T]) -> dict[str, list[Type[T]]]:
    eps = entry_points(group=PLUGIN_ENTRY_POINT_GROUP)

    return {
        ep.name: [cls for cls in ep.load() if issubclass(cls, typ)] for ep in eps
    }


__all__ = ["for_type"]