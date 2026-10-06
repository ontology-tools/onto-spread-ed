from dataclasses import asdict, dataclass, fields
from typing import Optional, get_args, overload

@dataclass
class TermIdentifierBase:
    id: str | None
    label: str | None

    def is_unresolved(self) -> bool:
        return self.id is None or self.label is None

    def is_resolved(self) -> bool:
        return not self.is_unresolved()
        
    def _cast[T: 'TermIdentifierBase'](self, cls: type[T]) -> T:
        return cls(**{f.name: getattr(self, f.name) for f in fields(cls) if f.init})
    
    def _assert_cast[T: 'TermIdentifierBase'](self, cls: type[T]) -> T:
        v = self._cast(cls)
        missing = [f.name for f in fields(cls) if getattr(v, f.name) is None and type(None) not in get_args(f.type)]
        if missing:
            raise ValueError(f"{type(self).__name__} cannot be cast to {cls.__name__}, missing {missing}: {self}")
        return v
        
    def as_resolved_identifier(self) -> Optional['TermIdentifier']:
        return self._cast(TermIdentifier) if self.id is not None and self.label is not None else None
        
    def as_with_id(self) -> Optional['TermIdentifierWithId']:
        return self._cast(TermIdentifierWithId) if self.id is not None else None
    
    def as_with_label(self) -> Optional['TermIdentifierWithLabel']:
        return self._cast(TermIdentifierWithLabel) if self.label is not None else None
    
    def assert_resolved_identifier(self) -> 'TermIdentifier':
        return self._assert_cast(TermIdentifier)
    
    def assert_id(self) -> 'TermIdentifierWithId':
        return self._assert_cast(TermIdentifierWithId)
    
    def assert_label(self) -> 'TermIdentifierWithLabel':
        return self._assert_cast(TermIdentifierWithLabel)

    def complement(self, other: 'TermIdentifierBase') -> None:
        selfd = asdict(self)
        otherd = asdict(other)
        for k, selfv in selfd.items():
            if k not in otherd:
                continue

            otherv = otherd[k]

            if selfv is None:
                setattr(self, k, otherv)
            elif otherv is not None and isinstance(otherv, list):
                selfv += otherv

    def __json__(self) -> dict:
        return self.__dict__

    def __eq__(self, other):
        if other is None or not isinstance(other, TermIdentifierBase):
            return False

        return all([self.id == other.id, self.label == other.label])

    def __hash__(self):
        return hash(self.id) + hash(self.label)

    def __lt__(self, other):
        if other is None or not isinstance(other, TermIdentifierBase):
            return False

        if self.id is None:
            return True

        if other.id is None:
            return False

        return self.id < other.id


@dataclass(eq=False)
class TermIdentifierWithId(TermIdentifierBase):
    id: str


@dataclass(eq=False)
class TermIdentifierWithLabel(TermIdentifierBase):
    label: str


@dataclass(eq=False)
class TermIdentifier(TermIdentifierWithId, TermIdentifierWithLabel):
    pass


@dataclass(eq=False)
class UnresolvedTermIdentifier(TermIdentifierBase):
    id: Optional[str] = None
    label: Optional[str] = None

@overload
def termid(*, id: str, label: str) -> TermIdentifier: ...
@overload
def termid(*, id: str, label: None = None) -> TermIdentifierWithId: ...
@overload
def termid(*, id: None = None, label: str) -> TermIdentifierWithLabel: ...
@overload
def termid(*, id: None = None, label: None = None) -> UnresolvedTermIdentifier: ...
def termid(*, id: Optional[str] = None, label: Optional[str] = None) -> TermIdentifierBase:
    if id is not None and label is not None:
        return TermIdentifier(id=id, label=label)
    elif id is not None:
        return TermIdentifierWithId(id=id, label=None)
    elif label is not None:
        return TermIdentifierWithLabel(id=None, label=label)
    
    return UnresolvedTermIdentifier(id=None, label=None)