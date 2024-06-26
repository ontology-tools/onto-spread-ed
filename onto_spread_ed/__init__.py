# Do the custom json serialization
from .custom_json import *  # noqa: F403, F401

from flask import Flask, session, g
from flask_cors import CORS
from flask_injector import FlaskInjector
from flask_sqlalchemy import SQLAlchemy

from . import config
from .database.User import User


def create_app(config_filename=None):
    # Clear type annotations to get around errors using url_for in jinja template
    # Source: https://github.com/python-injector/flask_injector/issues/78
    Flask.url_for.__annotations__ = {}
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)  # cross origin across all
    app.config['CORS_HEADERS'] = 'Content-Type'
    app.config['URL_PREFIX'] = config.URL_PREFIX
    CORS(app, resources={
        rf'{app.config["URL_PREFIX"]}/api/*': {
            'origins': '*'
        }
    })

    app.config.from_object(config)

    if config_filename is not None:
        app.config.from_pyfile(config_filename)

    from . import routes
    routes.init_app(app)

    from . import template_filters
    template_filters.init_app(app)

    @app.before_request
    def before_request(db: SQLAlchemy):
        g.user = None
        if 'user_id' in session:
            # print("user-id in session: ",session['user_id'])
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
