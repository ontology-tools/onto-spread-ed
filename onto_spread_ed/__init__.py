from flask import Flask, session, g
from flask_caching import Cache
from flask_cors import CORS
from flask_injector import FlaskInjector
from injector import Injector

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
    cache = Cache(app)

    for prefix in PREFIXES:
        cache.set("latestID" + prefix[0], 0)

    app.logger.info("cache initialised")

    from .AppModule import AppModule
    with app.app_context():
        injector = Injector([AppModule(app, cache)])

    from . import routes
    routes.init_app(app)

    @app.before_request
    def before_request():
        g.user = None
        if 'user_id' in session:
            # print("user-id in session: ",session['user_id'])
            g.user = User.query.get(session['user_id'])

    FlaskInjector(app=app, injector=injector)

    return app


