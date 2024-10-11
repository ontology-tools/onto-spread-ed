import json
import logging
from os import path
from typing import Optional, Dict, Any, List

import yaml
from dacite import from_dict
from flask_github import GitHub, GitHubError

from onto_spread_ed.model.RepositoryConfiguration import RepositoryConfiguration
from onto_spread_ed.services.ConfigurationService import ConfigurationService

REPOSITORY_CONFIG_PATH_PROP = "REPOSITORIES_REPOSITORY_CONFIG_PATH"
REPOSITORY_CONFIG_STARTUP_REPOSITORIES_PROP = "REPOSITORIES_REPOSITORY_CONFIG_STARTUP_REPOSITORIES_FILE"
BASE_URL_PROP = "REPOSITORIES_REPOSITORY_CONFIG_BASE_URL"
DEFAULT_HEADERS_PROP = "REPOSITORIES_REPOSITORY_CONFIG_REQUEST_HEADERS"
ALLOW_LOAD_REPOSITORIES_PROP = "REPOSITORIES_REPOSITORY_CONFIG_ALLOW_LOAD"
ALLOW_SAVE_REPOSITORIES_PROP = "REPOSITORIES_REPOSITORY_CONFIG_ALLOW_SAVE"


class RepositoryConfigurationService(ConfigurationService):
    _logger = logging.getLogger(__name__)
    _loaded_repositories: Dict[str, RepositoryConfiguration]

    def __init__(self, app_config: Dict[str, Any], gh: GitHub, *_args, **_kwargs):
        super().__init__(app_config)

        self._gh = gh

        self._config_path = app_config.get(REPOSITORY_CONFIG_PATH_PROP)
        self._base_url = app_config.get(BASE_URL_PROP)
        self._headers = app_config.get(DEFAULT_HEADERS_PROP)
        self._loaded_repositories = {}

        self._startup_repos_path = self.app_config.get(REPOSITORY_CONFIG_STARTUP_REPOSITORIES_PROP)

        for repo in self.startup_repositories():
            if self.get(repo) is None:
                self._logger.error(f"Failed to load default repo '{repo}'!")

    def startup_repositories(self) -> List[str]:
        file_name = self._startup_repos_path
        file_config = None
        if path.isfile(file_name):
            with open(file_name, "r") as f:
                if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                    file_config = yaml.safe_load(f)
                elif file_name.endswith(".json"):
                    file_config = json.load(f)
                else:
                    self._logger.error(
                        f"Failed to load default repositories to load from '{file_name}'. "
                        "Only yaml and json files are supported.")
        else:
            self._logger.error(f"Failed to load default repositories to load from '{file_name}'. Not a file.")

        if not isinstance(file_config, list) or not all(isinstance(v, str) for v in file_config):
            self._logger.error("Default repositories must be a list of strings.")
            return []

        return file_config

    def add_startup_repository(self, repo: str) -> bool:
        if not any(r.short_name == repo or r.full_name == repo or k == repo for (k, r) in
                   self._loaded_repositories.items()):
            self._logger.error(f"Repository '{repo}' is not loaded. Unloaded repositories cannot be added as default!")
            return False

        startups = [*self.startup_repositories(), repo]
        return self._save_startups(startups)

    def remove_startup_repository(self, repo: str) -> bool:
        startups = self.startup_repositories()

        if repo not in startups:
            return False

        startups.remove(repo)

        return self._save_startups(startups)

    def _save_startups(self, startups: List[str]) -> bool:
        file_name = self._startup_repos_path
        with open(file_name, "w") as f:
            if file_name.endswith(".yaml") or file_name.endswith(".yml"):
                yaml.safe_dump(startups, f)
            elif file_name.endswith(".json"):
                json.dump(startups, f)
            else:
                self._logger.error(
                    f"Failed to save default repositories to load from '{file_name}'. "
                    "Only yaml and json files are supported.")
                return False

        return True

    @property
    def loading_new_allowed(self) -> bool:
        return self.app_config.get(ALLOW_LOAD_REPOSITORIES_PROP)

    @property
    def changing_startup_allowed(self) -> bool:
        return self.app_config.get(ALLOW_SAVE_REPOSITORIES_PROP)

    def loaded_repositories(self) -> List[RepositoryConfiguration]:
        return list(self._loaded_repositories.values())

    def get_by_short_name(self, short_name: str) -> Optional[RepositoryConfiguration]:
        config = next((c for c in self._loaded_repositories.values() if c.short_name.lower() == short_name.lower()),
                      None)
        return config

    def get_by_full_name(self, full_name: str) -> Optional[RepositoryConfiguration]:
        url = self._base_url.format(full_name=full_name, path=self._config_path)
        config = self.get_by_url(url)
        if config is not None:
            config.full_name = full_name

        return config

    def get_by_url(self, url: str) -> Optional[RepositoryConfiguration]:
        loaded = self._loaded_repositories.get(url, None)
        if loaded is not None:
            return loaded

        try:
            response = self._gh.get(url, headers=self._headers)
        except GitHubError:
            return

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

        response = self._gh.get(url, headers=self._headers)

        if not response.ok:
            self._logger.warning(f"Could not get file '{path}': {response}")
            return None

        return response.text

    def unload(self, name: str) -> bool:
        key = next((k for k, v in self._loaded_repositories.items() if
                    v.full_name == name or v.short_name == name or k == name), None)
        if key is not None:
            del self._loaded_repositories[key]
            return True

        return False
