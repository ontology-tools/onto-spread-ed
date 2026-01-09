import typing

from flask import Flask, Request
from flask_executor import Executor
from flask_github import GitHub
from flask_injector import request
from flask_sqlalchemy import SQLAlchemy
from injector import Module, provider

from ose.injectables import ActiveBranch

from . import database, gh
from .OntologyDataStore import OntologyDataStore
from .PermissionManager import PermissionManager
from .SpreadsheetSearcher import SpreadsheetSearcher
from .services.ConfigurationService import ConfigurationService
from .services.FileCache import FileCache
from .services.LocalConfigurationService import LocalConfigurationService
from .services.OntoloyBuildService import OntologyBuildService
from .services.RepositoryConfigurationService import RepositoryConfigurationService
from .services.RobotOntologyBuildService import RobotOntologyBuildService


class AppModule(Module):
    """Configure the application."""

    def __init__(self):
        self._config = None

    def init_app(self, app):
        database.init_app(app)
        gh.init_app(app)

    @provider
    @request
    def active_branch(self, r: Request, config: ConfigurationService) -> ActiveBranch:
        repo_key = r.view_args.get("repo", r.view_args.get("repo_key", None))

        repo = config.get(repo_key) if repo_key is not None else None

        if repo_key is None or repo is None:
            raise ValueError("Cannot identify active repository to calculate active branch!")
        
        return r.args.get('branch', repo.main_branch)

    @provider
    @request
    def db(self) -> SQLAlchemy:
        # We configure the DB here, explicitly, as Flask-SQLAlchemy requires
        # the DB to be configured before request handlers are called.
        return database.db

    @provider
    @request
    def github(self) -> GitHub:
        return gh.github

    @provider
    @request
    def ontodb(self, config: ConfigurationService) -> OntologyDataStore:
        return OntologyDataStore(config)

    @provider
    @request
    def searcher(self, github: GitHub, config: ConfigurationService) -> SpreadsheetSearcher:
        return SpreadsheetSearcher(config, github)

    @provider
    @request
    def configuration_service(self, app: Flask, github: GitHub) -> ConfigurationService:
        if self._config is None:
            configuration_service = app.config.get("REPOSITORIES_SOURCE", "local")

            service = {
                "local": LocalConfigurationService,
                "repository": RepositoryConfigurationService
            }.get(configuration_service, LocalConfigurationService)

            self._config = service(app.config, github)

        return self._config

    @provider
    @request
    def executor(self, app: Flask) -> Executor:
        return Executor(app)

    @provider
    @request
    def ontology_builder(self) -> OntologyBuildService:
        return RobotOntologyBuildService()

    @provider
    @request
    def permission_manager(self, app: Flask) -> PermissionManager:
        return PermissionManager(app.config)

    @provider
    @request
    def file_cache(self, config: ConfigurationService) -> FileCache:
        life_time: typing.Union[int, None] = config.app_config.get("CACHE_LIFETIME", None)
        cache_dir = config.app_config.get("CACHE_DIR")

        if life_time is not None:
            return FileCache(cache_dir, life_time)
        else:
            return FileCache(cache_dir)
