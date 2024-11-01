import dataclasses
import typing

from typing import Generic, List

A = typing.TypeVar("A")


@dataclasses.dataclass
class Diff(Generic[A]):
    field: str
    a: A
    b: A
    change_type: str = "update"

    @property
    def old(self) -> A:
        return self.a

    @old.setter
    def old(self, value: A):
        self.a = value

    @property
    def new(self) -> A:
        return self.b

    @new.setter
    def new(self, value: A):
        self.b = value


SDiff = Diff[str]

PRIMITIVE_TYPES = (bool, str, int, float, type(None))


def diff(a, b, __path="") -> List[Diff]:
    if not (dataclasses.is_dataclass(a) or isinstance(a, dict)) or not \
            (dataclasses.is_dataclass(b) or isinstance(b, dict)):
        raise ValueError(f"Values must be dataclasses or dictionaries. a: '{type(a)}', b: '{type(b)}'")

    if type(a) != type(b):
        raise ValueError(f"Values must be of same type but '{type(a)}' != '{type(b)}'")

    results = []

    if dataclasses.is_dataclass(a):
        fields = [f.name for f in dataclasses.fields(a)]

        a = dataclasses.asdict(a)
        b = dataclasses.asdict(b)
    else:
        fields = a.keys()

    for f in fields:
        val_a = a[f]
        val_b = b[f]

        path = __path + ("." if __path else "") + f

        if isinstance(val_a, PRIMITIVE_TYPES):
            if val_a != val_b:
                results.append(Diff(path, val_a, val_b))
        elif isinstance(val_a, (list, tuple, set)):
            adds = [v for v in val_b if v not in val_a]
            removes = [v for v in val_a if v not in val_b]

            for v in adds:
                results.append(Diff(path, None, v, "add"))

            for v in removes:
                results.append(Diff(path, v, None, "remove"))
        else:
            results.extend(diff(val_a, val_b, path))

    return results
