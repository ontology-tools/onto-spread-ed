# Allow custom serialisation to json with __json__ function
from json import JSONEncoder

from flask_sqlalchemy import SQLAlchemy


def wrapped_default(self, obj):
    return getattr(obj.__class__, "__json__", wrapped_default.default)(obj)


wrapped_default.default = JSONEncoder().default

# apply the patch
JSONEncoder.original_default = JSONEncoder.default
JSONEncoder.default = wrapped_default

from flask import Flask, session, g
from flask_cors import CORS
from flask_injector import FlaskInjector

from .config import PREFIXES

from . import config
from .database.User import User


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    CORS(app)  # cross origin across all
    app.config['CORS_HEADERS'] = 'Content-Type'
    CORS(app, resources={
        r"/api/*": {
            "origins": "*"
        }
    })

    app.config.from_object(config)

    app.logger.info("cache initialised")

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
