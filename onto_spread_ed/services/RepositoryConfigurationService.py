import logging
from typing import Optional, Dict, Any, List

import requests
import yaml
from dacite import from_dict

from onto_spread_ed.model.RepositoryConfiguration import RepositoryConfiguration
from onto_spread_ed.services.ConfigurationService import ConfigurationService

DEFAULT_REPOSITORY_CONFIG_PATH_PROP = "REPOSITORY_CONFIG_DEFAULT_PATH"
DEFAULT_REPOSITORY_CONFIG_PATH = ".onto-ed/config.yaml"

DEFAULT_REPOSITORIES_PROP = "REPOSITORY_CONFIG_DEFAULT_REPOSITORIES"
DEFAULT_REPOSITORIES: List[str] = []

BASE_URL_PROP = "REPOSITORY_CONFIG_BASE_URL"
BASE_URL = "https://api.github.com/repos/{full_name}/contents/{path}"

DEFAULT_HEADERS_PROP = "REPOSITORY_CONFIG_REQUEST_HEADERS"
DEFAULT_HEADERS: Dict[str, str] = {
    "Accept": "application/vnd.github.raw+json",
}


class RepositoryConfigurationService(ConfigurationService):
    _logger = logging.getLogger(__name__)
    _loaded_repositories: Dict[str, RepositoryConfiguration]

    def __init__(self, app_config: Dict[str, Any]):
        super().__init__(app_config)

        self._default_config_path = app_config.get(DEFAULT_REPOSITORY_CONFIG_PATH_PROP, DEFAULT_REPOSITORY_CONFIG_PATH)
        self._base_url = app_config.get(BASE_URL_PROP, BASE_URL)
        self._headers = app_config.get(DEFAULT_HEADERS_PROP, DEFAULT_HEADERS)
        self._loaded_repositories = {}

        default_repos = self.app_config.get(DEFAULT_REPOSITORIES_PROP, DEFAULT_REPOSITORIES)

        for repo in default_repos:
            self.get(repo)

    def loaded_repositories(self) -> List[RepositoryConfiguration]:
        return list(self._loaded_repositories.values())

    def get_by_short_name(self, short_name: str) -> Optional[RepositoryConfiguration]:
        config = next((c for c in self._loaded_repositories.values() if c.short_name == short_name), None)
        return config

    def get_by_full_name(self, full_name: str) -> Optional[RepositoryConfiguration]:
        url = self._base_url.format(full_name=full_name, path=self._default_config_path)
        return self.get_by_url(url)

    def get_by_url(self, url: str) -> Optional[RepositoryConfiguration]:
        loaded = self._loaded_repositories.get(url, None)
        if loaded is not None:
            return loaded

        response = requests.get(url, headers=self._headers)

        if not response.ok:
            self._logger.warning(f"Could not get repository configuration from '{url}': {response}")
            return None

        try:
            data = yaml.safe_load(response.text)
        except yaml.YAMLError as e:
            self._logger.warning(f"Could not parse repository configuration from '{url}': {e}")
            return None

        try:
            configuration = from_dict(RepositoryConfiguration, data)
        except Exception as e:
            self._logger.warning(f"Could not parse repository configuration from '{url}': {e}")
            return None

        self._loaded_repositories[url] = configuration

        return configuration

    def get_file(self, config: RepositoryConfiguration, path: str) -> Optional[str]:
        url = self._base_url.format(full_name=config.full_name, path=path)

        response = requests.get(url, headers=self._headers)

        if not response.ok:
            self._logger.warning(f"Could not get file '{path}': {response}")
            return None

        return response.text




