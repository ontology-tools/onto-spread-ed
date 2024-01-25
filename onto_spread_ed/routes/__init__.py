from flask import Flask


def init_app(app: Flask):
    from .auth import bp as auth
    from .main import bp as main
    from .edit import bp as edit
    from .search import bp as search
    from .visualize import bp as visualize
    from .admin import bp as admin

    from .api import blueprints as api_blueprints

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(edit)
    app.register_blueprint(search)
    app.register_blueprint(visualize)
    app.register_blueprint(admin)

    for bp in api_blueprints:
        app.register_blueprint(bp)
