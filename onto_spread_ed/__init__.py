# Do the custom json serialization
import json
from os import path

import yaml
from flask import Flask, session, g
from flask_cors import CORS
from flask_injector import FlaskInjector
from flask_sqlalchemy import SQLAlchemy

from . import default_config
from .custom_json import *  # noqa: F403, F401
from .database.User import User


def load_config(app: Flask, config_filename):
    # load default
    app.config.from_object(default_config)

    # load yaml
    if path.exists(config_filename):
        file_config = None
        if path.isfile(config_filename):
            with open(config_filename, "r") as f:
                if config_filename.endswith(".yaml") or config_filename.endswith(".yml"):
                    file_config = yaml.safe_load(f)
                elif config_filename.endswith(".json"):
                    file_config = json.load(f)
                else:
                    app.logger.error(f"Failed to load configuration from '{config_filename}'."
                                     " Only yaml and json files are supported.")
        else:
            app.logger.error(f"Failed to load configuration from '{config_filename}'. Not a file.")

        if file_config is not None:
            config_obj = {
                k.replace("-", "_").upper(): v for k, v in file_config.items()
            }

            repository_obj = dict()
            if "repositories" in file_config:
                repositories = file_config['repositories']
                repository_obj = {
                    f"REPOSITORIES_{repositories['source'].upper()}_CONFIG_{k.replace('-', '_').upper()}": v
                    for k, v in repositories.get('data', dict()).items()
                }
                repository_obj["REPOSITORIES_SOURCE"] = file_config['repositories']['source']
                del config_obj['REPOSITORIES']

            config_obj = {**config_obj, **repository_obj}

            app.config.from_mapping(config_obj)

    # load from env
    app.config.from_prefixed_env()
    app.config.from_prefixed_env("OSE")

    # add aliases
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get("DATABASE_URI")


def create_app(config_filename=None):
    if config_filename is None:
        config_filename = "config.yaml"

    # Clear type annotations to get around errors using url_for in jinja template
    # Source: https://github.com/python-injector/flask_injector/issues/78
    Flask.url_for.__annotations__ = {}
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)  # cross origin across all

    load_config(app, config_filename)

    CORS(app, resources={
        rf'{app.config["URL_PREFIX"]}/api/*': {
            'origins': '*'
        }
    })

    from . import routes
    routes.init_app(app)

    from . import template_filters
    template_filters.init_app(app)

    @app.before_request
    def before_request(db: SQLAlchemy):
        g.user = None
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            g.user = user
            if user is not None:
                db.session.expunge(user)

    from .AppModule import AppModule

    module = AppModule()
    with app.app_context():
        module.init_app(app)

    FlaskInjector(app=app, modules=[module])

    return app
