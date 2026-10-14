from flask import Blueprint, request, session, redirect, current_app, jsonify
from flask_github import GitHub

from ..guards.verify_login import verify_logged_in

bp = Blueprint("authentication", __name__)


@bp.route('/login')
def login(github: GitHub):
    if session.get('user_id', None) is not None:
        session.pop('user_id', None)  # Could be stale
        
    session['next'] = request.args.get('next', None)

    return github.authorize(scope="user,repo,workflow")


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(f"{current_app.config['URL_PREFIX']}/loggedout")


@bp.route('/user')
@verify_logged_in
def user(github: GitHub):
    return jsonify(github.get('/user'))
