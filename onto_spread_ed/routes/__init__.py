from flask import Flask


def init_app(app: Flask):
    from .release import bp as release
    from .verify import bp as verify
    from .auth import bp as auth
    from .main import bp as main
    from .edit import bp as edit
    from .search import bp as search
    from .visualize import bp as visualize

    app.register_blueprint(release)
    app.register_blueprint(verify)
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(edit)
    app.register_blueprint(search)
    app.register_blueprint(visualize)

