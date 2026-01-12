import typing

from flask import Flask
from flask_executor import Executor
from flask_github import GitHub
from flask_injector import request
from flask_sqlalchemy import SQLAlchemy
from injector import Injector, Module, provider, singleton

from ose_core.services.PluginService import PluginService

from . import database, gh
from .OntologyDataStore import OntologyDataStore
from .PermissionManager import PermissionManager
from .SpreadsheetSearcher import SpreadsheetSearcher
from ose_core.services.ConfigurationService import ConfigurationService
from ose_core.services.FileCache import FileCache
from ose_core.services.LocalConfigurationService import LocalConfigurationService
from ose_core.services.OntoloyBuildService import OntologyBuildService
from ose_core.services.RepositoryConfigurationService import RepositoryConfigurationService
from ose_core.services.RobotOntologyBuildService import RobotOntologyBuildService


class AppModule(Module):
    """Configure the application."""

    def init_app(self, app: Flask):
        database.init_app(app)
        gh.init_app(app)

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
    @singleton
    def ontodb(self, config: ConfigurationService) -> OntologyDataStore:
        return OntologyDataStore(config)

    @provider
    @singleton
    def searcher(self, github: GitHub, config: ConfigurationService) -> SpreadsheetSearcher:
        return SpreadsheetSearcher(config, github)

    @provider
    @singleton
    def configuration_service(self, app: Flask, github: GitHub) -> ConfigurationService:
        configuration_service = app.config.get("REPOSITORIES_SOURCE", "local")

        service = {
            "local": LocalConfigurationService,
            "repository": RepositoryConfigurationService
        }.get(configuration_service, LocalConfigurationService)

        return service(app.config, github)

    @provider
    @singleton
    def executor(self, app: Flask) -> Executor:
        return Executor(app)

    @provider
    @singleton
    def ontology_builder(self) -> OntologyBuildService:
        return RobotOntologyBuildService()

    @provider
    @singleton
    def permission_manager(self, app: Flask) -> PermissionManager:
        return PermissionManager(app.config)

    @provider
    @singleton
    def file_cache(self, config: ConfigurationService) -> FileCache:
        life_time: typing.Union[int, None] = config.app_config.get("CACHE_LIFETIME", None)
        cache_dir = config.app_config.get("CACHE_DIR")

        if life_time is not None:
            return FileCache(cache_dir, life_time)
        else:
            return FileCache(cache_dir)
        
    @provider
    @singleton
    def plugin_service(self, config: ConfigurationService, injector: Injector) -> PluginService:
        plugin_service = PluginService(config, injector)
        plugin_service.load_plugins()
        return plugin_service
