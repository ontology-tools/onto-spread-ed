from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker

from .Base import Base


def init_app(app):
    db = SQLAlchemy(app)
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=db.engine))
    Base.query = db_session.query_property()
    Base.metadata.create_all(db.engine)
    return db
