import abc
from typing import Dict, Optional, Any, List

from ose.project import Project


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
    def loaded_repositories(self) -> List[Project]:
        ...

    @abc.abstractmethod
    def get_by_short_name(self, short_name: str) -> Optional[Project]:
        ...

    @abc.abstractmethod
    def get_by_full_name(self, full_name: str) -> Optional[Project]:
        ...

    @abc.abstractmethod
    def get_by_url(self, url: str) -> Optional[Project]:
        ...

    @abc.abstractmethod
    def local_path(self, project: Project) -> str:
        """Directory of the local clone of the repository of `project`"""
        ...

    @abc.abstractmethod
    def unload(self, name: str) -> bool:
        ...

    def get_file(self, config: Project, path: str) -> Optional[str]:
        file = self.get_file_raw(config, path)
        if file is not None:
            return file.decode()

        return None

    @abc.abstractmethod
    def get_file_raw(self, config: Project, path: str) -> Optional[bytes]:
        ...

    def get(self, name: str) -> Optional[Project]:
        parts = name.split("/")
        if len(parts) == 1:
            return self.get_by_short_name(name)
        elif len(parts) == 2:
            return self.get_by_full_name(name)
        else:
            return self.get_by_url(name)

    def replace(self, project: Project) -> bool:
        """Replaces the loaded project of the same repository with `project`, e.g. after its configuration was saved"""
        return False

    def add_startup_repository(self, repo: str) -> bool:
        return False

    def remove_startup_repository(self, repo: str) -> bool:
        return False

    def startup_repositories(self) -> List[str]:
        return []

    @abc.abstractmethod
    def reload(self) -> None:
        ...
