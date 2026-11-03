from os.path import join, dirname

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

# Get the migrations directory path relative to this package
_migrations_dir = join(dirname(__file__),  'migrations')


def init_app(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db, directory=_migrations_dir)

    @app.after_request
    def after_request(response):
        db.session.remove()
        return response

    @app.teardown_request
    def teardown_request_func(error):
        try:
            db.session.remove()
        except Exception as e:
            app.logger.error(f"Error in teardown_request_func: {e}")
        if error:
            app.logger.error(str(error))

    return db
