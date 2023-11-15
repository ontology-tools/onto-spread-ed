import functools

from flask import g, redirect, url_for, abort

from config import USERS_METADATA


def verify_admin(fn):
    """
    Decorator used to make sure that the user is logged in
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # If the user is not logged in, then redirect him to the "logged out" page:
        if not g.user:
            return redirect(url_for("login"))
        if not USERS_METADATA.get(g.user.github_login, {}).get("admin", False):
            abort(403, "You do not have sufficient permissions!")
        return fn(*args, **kwargs)

    return wrapped
