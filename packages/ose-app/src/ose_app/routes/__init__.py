from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from ose_app.guards.api_request import is_api_request


def _handle_http_exception(e: HTTPException):
    """`/api` never renders HTML: HTTP errors (404, 405, 500, ...) become `{success: false, error}`."""
    if not is_api_request():
        return e
    status = e.code or 500
    error = "Internal server error" if status >= 500 else (e.description or e.name)
    response = jsonify({"success": False, "error": error})
    response.status_code = status
    allow = e.get_response().headers.get("Allow")
    if allow:
        response.headers["Allow"] = allow
    return response


def init_app(app: Flask):
    from .auth import bp as auth
    from .status import bp as status

    from .api import blueprints as api_blueprints

    app.register_blueprint(auth)
    app.register_blueprint(status)

    app.register_error_handler(HTTPException, _handle_http_exception)

    for bp in api_blueprints:
        app.register_blueprint(bp)

    # Catch-all, must be registered last
    from .spa import bp as spa
    app.register_blueprint(spa)
