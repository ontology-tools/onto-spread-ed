import abc
from typing import Dict, Optional, Any, List

from onto_spread_ed.model.RepositoryConfiguration import RepositoryConfiguration


class ConfigurationService(abc.ABC):
    _app_config: Dict[str, Any]

    def __init__(self, app_config: Dict[str, Any]):
        self._app_config = app_config

    @abc.abstractmethod
    def loaded_repositories(self) -> List[RepositoryConfiguration]:
        ...

    @abc.abstractmethod
    def get_by_short_name(self, short_name: str) -> Optional[RepositoryConfiguration]:
        ...

    @abc.abstractmethod
    def get_by_full_name(self, full_name: str) -> Optional[RepositoryConfiguration]:
        ...

    @abc.abstractmethod
    def get_by_url(self, url: str) -> Optional[RepositoryConfiguration]:
        ...

    def get(self, name: str) -> Optional[RepositoryConfiguration]:
        parts = name.split("/")
        if len(parts) == 1:
            return self.get_by_short_name(name)
        elif len(parts) == 2:
            return self.get_by_full_name(name)
        else:
            return self.get_by_url(name)

    @property
    def app_config(self) -> Dict[str, Any]:
        return self._app_config

    @abc.abstractmethod
    def get_file(self, config: RepositoryConfiguration, path: str) -> Optional[str]:
        ...
