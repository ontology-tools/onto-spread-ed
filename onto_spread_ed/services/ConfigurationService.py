import abc
from typing import Dict, Optional, Any

from onto_spread_ed.model.RepositoryConfiguration import RepositoryConfiguration


class ConfigurationService(abc.ABC):
    _app_config: Dict[str, Any]

    def __init__(self, app_config: Dict[str, Any]):
        self._app_config = app_config

    @abc.abstractmethod
    def loaded_repositories(self) -> Dict[str, RepositoryConfiguration]:
        pass

    @abc.abstractmethod
    def get_by_short_name(self, short_name: str) -> Optional[RepositoryConfiguration]:
        pass

    @abc.abstractmethod
    def get_by_full_name(self, full_name: str) -> Optional[RepositoryConfiguration]:
        pass

    @abc.abstractmethod
    def get_by_url(self, url: str) -> Optional[RepositoryConfiguration]:
        pass

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
