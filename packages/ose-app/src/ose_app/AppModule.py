import typing

from flask import Flask
from flask_injector import request
from flask_sqlalchemy import SQLAlchemy
from github import Github
from injector import Injector, Module, provider, singleton

from . import database
from .PermissionManager import PermissionManager
from .SpreadsheetSearcher import SpreadsheetSearcher
from .services.ConfigurationService import ConfigurationService
from .services.FileCache import FileCache
from .services.GithubService import GithubService
from .services.PluginService import PluginService
from .services.RepositoryConfigurationService import RepositoryConfigurationService


class AppModule(Module):
    """Configure the application."""

    def init_app(self, app: Flask):
        database.init_app(app)

    @provider
    @request
    def db(self) -> SQLAlchemy:
        # We configure the DB here, explicitly, as Flask-SQLAlchemy requires
        # the DB to be configured before request handlers are called.
        return database.db

    @provider
    @singleton
    def github_service(self, app: Flask) -> GithubService:
        return GithubService(app.config.get("GITHUB_CLIENT_ID"), app.config.get("GITHUB_CLIENT_SECRET"))

    @provider
    @request
    def github(self, github_service: GithubService) -> Github:
        """Client acting on behalf of the user of the current request"""
        return github_service.current_client()

    @provider
    @singleton
    def searcher(self, github_service: GithubService, config: ConfigurationService) -> SpreadsheetSearcher:
        return SpreadsheetSearcher(config, github_service)

    @provider
    @singleton
    def configuration_service(self, app: Flask, github_service: GithubService) -> ConfigurationService:
        return RepositoryConfigurationService(app.config, github_service)

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
    def plugin_service(self, injector: Injector) -> PluginService:
        plugin_service = PluginService(injector)
        plugin_service.discover_all()
        return plugin_service
