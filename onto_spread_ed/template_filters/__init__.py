from flask import Flask


def init_app(app: Flask):
    from .css_safe import css_safe
    app.jinja_env.filters["css_safe"] = css_safe
