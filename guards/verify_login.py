import functools

from flask import g, redirect, url_for


def verify_logged_in(fn):
    """
    Decorator used to make sure that the user is logged in
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # If the user is not logged in, then redirect him to the "logged out" page:
        if not g.user:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapped
