import abc
from typing import Dict, Optional, Any, List

from ose_core.model.RepositoryConfiguration import RepositoryConfiguration


class ConfigurationService(abc.ABC):
    _app_config: Dict[str, Any]

    def __init__(self, app_config: Dict[str, Any]):
        self._app_config = app_config

    @property
    def app_config(self) -> Dict[str, Any]:
        return self._app_config

    @property
    def loading_new_allowed(self) -> bool:
        return False

    @property
    def changing_startup_allowed(self) -> bool:
        return False

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

    @abc.abstractmethod
    def unload(self, name: str) -> bool:
        ...

    def get_file(self, config: RepositoryConfiguration, path: str) -> Optional[str]:
        file = self.get_file_raw(config, path)
        if file is not None:
            return file.decode()

        return None

    @abc.abstractmethod
    def get_file_raw(self, config: RepositoryConfiguration, path: str) -> Optional[bytes]:
        ...

    def get(self, name: str) -> Optional[RepositoryConfiguration]:
        parts = name.split("/")
        if len(parts) == 1:
            return self.get_by_short_name(name)
        elif len(parts) == 2:
            return self.get_by_full_name(name)
        else:
            return self.get_by_url(name)

    def add_startup_repository(self, repo: str) -> bool:
        return False

    def remove_startup_repository(self, repo: str) -> bool:
        return False

    def startup_repositories(self) -> List[str]:
        return []

    @abc.abstractmethod
    def reload(self) -> None:
        ...
