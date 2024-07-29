from flask import Flask
from flask_executor import Executor
from flask_github import GitHub
from flask_injector import request
from flask_sqlalchemy import SQLAlchemy
from injector import Module, provider

from . import database, gh
from .OntologyDataStore import OntologyDataStore
from .SpreadsheetSearcher import SpreadsheetSearcher
from .services.ConfigurationService import ConfigurationService
from .services.LocalConfigurationService import LocalConfigurationService
from .services.OntoloyBuildService import OntologyBuildService
from .services.RobotOntologyBuildService import RobotOntologyBuildService


class AppModule(Module):
    """Configure the application."""

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
    def github(self, app: Flask) -> GitHub:
        return gh.github

    @provider
    @request
    def ontodb(self, app: Flask, config: ConfigurationService) -> OntologyDataStore:
        return OntologyDataStore(config)

    @provider
    @request
    def searcher(self, app: Flask, github: GitHub, config: ConfigurationService) -> SpreadsheetSearcher:
        return SpreadsheetSearcher(config, github)

    @provider
    @request
    def configuration_service(self, app: Flask) -> ConfigurationService:
        return LocalConfigurationService(app.config)

    @provider
    @request
    def executor(self, app: Flask) -> Executor:
        return Executor(app)

    @provider
    @request
    def ontology_builder(self) -> OntologyBuildService:
        return RobotOntologyBuildService()
