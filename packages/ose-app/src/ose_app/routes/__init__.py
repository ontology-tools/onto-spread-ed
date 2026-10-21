from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


def _is_api_request() -> bool:
    return request.path == "/api" or request.path.startswith("/api/")


def _handle_http_exception(e: HTTPException):
    """`/api` never renders HTML: HTTP errors (404, 405, 500, ...) become `{success: false, error}`."""
    if not _is_api_request():
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
