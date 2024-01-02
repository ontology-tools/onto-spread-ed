from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_app(app):
    # db_session = scoped_session(sessionmaker(autocommit=False,
    #                                          autoflush=False,
    #                                          bind=db.engine))
    # Base.query = db_session.query_property()
    # Base.metadata.create_all(db.engine)
    db.init_app(app)

    # from .Release import Release
    # from .User import User
    from .Base import Base

    Base.metadata.create_all(db.engine)

    return db
