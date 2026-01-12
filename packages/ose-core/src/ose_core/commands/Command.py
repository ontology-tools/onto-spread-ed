import abc
from typing import Tuple

from .CommandContext import CommandContext
from ..model.Result import Result


class CommandCanceledException(Exception):
    pass


class Command(abc.ABC):
    _context: CommandContext

    def __init__(self, context: CommandContext):
        self._context = context

    def run(self, **kwargs) -> Tuple[Result, bool]:
        ...

    def _raise_if_canceled(self):
        if self._context.canceled():
            raise CommandCanceledException("Release has been canceled!")

    def _local_name(self, remote_name, file_ending=None) -> str:
        return self._context.local_name(remote_name, file_ending)

    def cleanup(self):
        pass
