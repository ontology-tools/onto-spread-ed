# Allow custom serialisation to json with __json__ function
import dataclasses
from datetime import datetime
from json import JSONEncoder


def dump_default(obj):
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return getattr(obj.__class__, "__json__", dump_default.default)(obj)


def wrapped_default(self, obj):
    return dump_default(obj)


dump_default.default = JSONEncoder().default

# apply the patch
JSONEncoder.original_default = JSONEncoder.default
JSONEncoder.default = wrapped_default
