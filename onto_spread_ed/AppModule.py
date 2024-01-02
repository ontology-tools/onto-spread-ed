from flask import Flask
from flask_caching import Cache
from flask_executor import Executor
from flask_github import GitHub
from flask_injector import request
from flask_sqlalchemy import SQLAlchemy
from injector import Module, singleton, Binder, provider

from . import database
from . import gh
from .OntologyDataStore import OntologyDataStore
from .SpreadsheetSearcher import SpreadsheetSearcher


class AppModule(Module):
    def __init__(self, cache: Cache):
        self.cache = cache

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
    def ontodb(self, app: Flask) -> OntologyDataStore:
        return OntologyDataStore(app.config)

    @provider
    @request
    def searcher(self, app: Flask, github: GitHub) -> SpreadsheetSearcher:
        return SpreadsheetSearcher(self.cache, app.config, github)

    @provider
    @request
    def executor(self, app: Flask) -> Executor:
        return Executor(app)


