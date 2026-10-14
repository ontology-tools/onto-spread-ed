from flask import request


def is_api_request() -> bool:
    """Whether the current request targets the JSON API (`/api/...`), which never redirects or renders HTML."""
    return request.path == "/api" or request.path.startswith("/api/")
