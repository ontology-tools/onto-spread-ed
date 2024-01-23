import functools

from flask import g, redirect, url_for, abort, current_app


def verify_admin(fn):
    """
    Decorator used to make sure that the user is logged in
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # If the user is not logged in, then redirect him to the "logged out" page:
        if not g.user:
            return redirect(url_for("authentication.login"))
        if not current_app.config['USERS_METADATA'].get(g.user.github_login, {}).get("admin", False):
            abort(403, "You do not have sufficient permissions!")
        return fn(*args, **kwargs)

    return wrapped
