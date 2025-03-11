from flask import Blueprint, session, redirect, url_for, render_template, jsonify
from flask_github import GitHub

from ..guards.verify_login import verify_logged_in

bp = Blueprint("authentication", __name__, template_folder="../templates")


@bp.route('/login')
def login(github: GitHub):
    if session.get('user_id', None) is not None:
        session.pop('user_id', None)  # Could be stale

    return github.authorize(scope="user,repo,workflow")


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('authentication.loggedout'))


@bp.route("/loggedout")
def loggedout():
    """
    Displays the page to be shown to logged out users.
    """
    return render_template("loggedout.html")


@bp.route("/forbidden")
def forbidden():
    """
    Displays the page to be shown to logged out users.
    """
    return render_template("forbidden.html")


@bp.route('/user')
@verify_logged_in
def user(github: GitHub):
    return jsonify(github.get('/user'))
