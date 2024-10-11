from flask import Flask
from flask_executor import Executor
from flask_github import GitHub
from flask_injector import request
from flask_sqlalchemy import SQLAlchemy
from injector import Module, provider

from . import database, gh
from .OntologyDataStore import OntologyDataStore
from .PermissionManager import PermissionManager
from .SpreadsheetSearcher import SpreadsheetSearcher
from .services.ConfigurationService import ConfigurationService
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
