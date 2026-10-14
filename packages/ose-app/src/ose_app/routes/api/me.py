from flask import Blueprint, current_app, g, jsonify

from ose_app.PermissionManager import PERMISSION_IMPLICATIONS, PermissionManager
from ose_app.helpers import all_initials, user_initials
from ose_app.services.ConfigurationService import ConfigurationService

bp = Blueprint("api_me", __name__, url_prefix="/api/me")


@bp.route("", methods=["GET"])
def me(permission_manager: PermissionManager, config: ConfigurationService):
    """Current user and app info. Public: answers also for logged out users."""
    data = dict(
        logged_in=g.user is not None,
        app_title=current_app.config.get("APP_TITLE"),
        app_version=current_app.config.get("APP_VERSION"),
        environment=current_app.config.get("ENVIRONMENT"),
        url_prefix=current_app.config.get("URL_PREFIX", ""),
    )

    if g.user is not None:
        permissions = permission_manager.user_permission(g.user.github_login)
        if "admin" in permissions:  # admin implicitly has all permissions
            permissions = permissions | set(PERMISSION_IMPLICATIONS.keys())

        data.update(
            login=g.user.github_login,
            initials=user_initials(config),
            permissions=sorted(permissions),
            all_initials=all_initials(config),
        )

    return jsonify(data)
