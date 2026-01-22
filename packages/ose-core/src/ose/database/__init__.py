from os.path import join, dirname

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()

# Get the migrations directory path relative to this package
_migrations_dir = join(dirname(__file__),  'migrations')


def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db, directory=_migrations_dir)

    return db
