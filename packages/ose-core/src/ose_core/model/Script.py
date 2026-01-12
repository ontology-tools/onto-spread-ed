from abc import ABC, abstractmethod
from dataclasses import dataclass
import inspect
import logging
from typing import Any, Callable, Coroutine
from ose_core.model.ScriptArgument import ScriptArgument
import collections

def _not_implemented(*args, **kwargs):
    raise NotImplementedError()

class Script(ABC):
    _logger = logging.getLogger(__name__)
    
    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def title(self) -> str:
        raise NotImplementedError
    
    @property
    def arguments(self) -> list[ScriptArgument]:
        try:
            signature = inspect.signature(self.run)
            return [
                ScriptArgument(
                    name=p.name,
                    description=p.annotation.__metadata__[0] if hasattr(p.annotation, "__metadata__") else p.name,
                    default=p.default if p.default != inspect.Parameter.empty else None,
                    type="string"  # Could be improved by mapping types
                    )
                for p in signature.parameters.values()
            ]
        except ValueError:
            self._logger.warning(f"Could not inspect signature of script '{self.id}' to determine arguments.")
            return []
    
    run: Callable[..., Coroutine[None, None, str] | str] = _not_implemented