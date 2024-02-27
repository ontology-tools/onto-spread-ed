# Allow custom serialisation to json with __json__ function
import dataclasses
from json import JSONEncoder


def wrapped_default(self, obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)


wrapped_default.default = JSONEncoder().default

# apply the patch
JSONEncoder.original_default = JSONEncoder.default
JSONEncoder.default = wrapped_default
