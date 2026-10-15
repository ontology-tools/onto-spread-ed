import functools
from typing import Optional, Sequence

from flask import g, jsonify

from ose_app.PermissionManager import PermissionManager


def requires_permissions(*permissions: str, any_of: Optional[Sequence[str]] = None,
                         all_of: Optional[Sequence[str]] = None):
    if int(len(permissions) > 0) + int(any_of is not None) + int(all_of is not None) != 1:
        raise ValueError("Exactly on of a list of permissions or 'any_of' or 'all_of' must be specified.")

    if len(permissions) > 0:
        all_of = permissions

    def with_permissions_decorator(fn):
        """
        Decorator used to make sure that the user has the proper permission
        """

        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            permission_manager = kwargs.pop("__permission_manager")

            if not g.user:
                return jsonify({"success": False, "error": "You are not logged in!"}), 401

            user_name = g.user.github_login

            permitted = False
            if any_of is not None:
                permitted = any(permission_manager.has_permissions(user_name, p) for p in any_of)
            elif all_of is not None:
                permitted = permission_manager.has_permissions(user_name, *all_of)

            if not permitted:
                return jsonify({"success": False, "error": "You don't have permission to access this page!"}), 403

            return fn(*args, **kwargs)

        wrapped.__annotations__['__permission_manager'] = PermissionManager
        return wrapped

    return with_permissions_decorator
