import abc
from typing import Optional


class CommandContext(abc.ABC):
    @abc.abstractmethod
    def canceled(self) -> bool:
        ...

    @abc.abstractmethod
    def local_name(self, remote_name, file_ending=None) -> str:
        ...

    @abc.abstractmethod
    def save_file(self, file: str, temporary: Optional[bool] = None, **kwargs):
        ...
