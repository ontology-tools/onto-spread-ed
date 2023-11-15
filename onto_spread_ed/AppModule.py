from flask import Flask
from flask_caching import Cache
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from injector import Module, singleton

from . import database
from . import gh
from .OntologyDataStore import OntologyDataStore
from .SpreadsheetSearcher import SpreadsheetSearcher


class AppModule(Module):
    def __init__(self, app: Flask, cache: Cache):
        self.app = app
        self.cache = cache

    """Configure the application."""

    def configure(self, binder):
        # We configure the DB here, explicitly, as Flask-SQLAlchemy requires
        # the DB to be configured before request handlers are called.
        db = database.init_app(self.app)
        binder.bind(SQLAlchemy, to=db, scope=singleton)

        github = gh.init_app(self.app)
        binder.bind(GitHub, to=github, scope=singleton)

        ontodb = OntologyDataStore(self.app.config)
        binder.bind(OntologyDataStore, to=ontodb, scope=singleton)

        searcher = SpreadsheetSearcher(self.cache, self.app.config, github)
        binder.bind(SpreadsheetSearcher, to=searcher, scope=singleton)
