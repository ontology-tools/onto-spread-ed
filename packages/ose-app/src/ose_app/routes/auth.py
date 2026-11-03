from flask import Blueprint, request, session, redirect, current_app, g, url_for
from flask_sqlalchemy import SQLAlchemy

from ose_app.database.User import User
from ose_app.services.GithubService import GithubService

bp = Blueprint("authentication", __name__)


@bp.route('/login')
def login(github_service: GithubService):
    if session.get('user_id', None) is not None:
        session.pop('user_id', None)  # Could be stale
        
    session['next'] = request.args.get('next', None)

    return redirect(github_service.authorize_url(scope="user,repo,workflow"))


@bp.route('/github-callback')
def authorized(db: SQLAlchemy, github_service: GithubService):
    next_url = session.pop('next', None) or f"{current_app.config['URL_PREFIX']}/"
    access_token = github_service.exchange_code(request.args.get('code'))
    if access_token is None:
        current_app.logger.warning("Authorization failed.")
        return redirect(url_for('authentication.logout'))

    user = db.session.query(User).filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
    # Not necessary to get these details here
    # but it helps humans to identify users easily.

    g.user = user
    github_user = github_service.client(access_token).get_user()
    user.github_id = github_user.id
    user.github_login = github_user.login
    user.github_access_token = access_token
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id

    db.session.expunge(user)

    return redirect(next_url)


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(f"{current_app.config['URL_PREFIX']}/loggedout")
