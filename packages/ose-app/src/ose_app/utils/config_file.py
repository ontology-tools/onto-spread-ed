from typing import Any


def apply_changes(document: Any, old: Any, new: Any) -> Any:
    """Write explicit model values while keeping extension fields."""
    if isinstance(document, dict) and isinstance(old, dict) and isinstance(new, dict):
        return {
            **{key: value for key, value in document.items() if key not in old},
            **{key: apply_changes(document.get(key), old.get(key), value) for key, value in new.items()},
        }

    if isinstance(document, list) and isinstance(old, list) and isinstance(new, list) and \
            len(document) == len(old) == len(new):
        return [apply_changes(d, o, n) for d, o, n in zip(document, old, new)]

    return new
