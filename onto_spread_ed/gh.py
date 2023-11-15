from flask import Flask, request, url_for, redirect, g, session
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy

from .database.User import User


def init_app(app: Flask):
    github = GitHub(app)

    @github.access_token_getter
    def token_getter():
        user = g.user
        if user is not None:
            return user.github_access_token

    @app.route('/github-callback')
    @github.authorized_handler
    def authorized(access_token, db: SQLAlchemy):
        next_url = request.args.get('next') or url_for('main.home')
        if access_token is None:
            app.logger.warning("Authorization failed.")
            return redirect(url_for('authentication.logout'))

        user = User.query.filter_by(github_access_token=access_token).first()
        if user is None:
            user = User(access_token)
        # Not necessary to get these details here
        # but it helps humans to identify users easily.
        g.user = user
        github_user = github.get('/user')
        user.github_id = github_user['id']
        user.github_login = github_user['login']
        user.github_access_token = access_token
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        return redirect(next_url)

    @app.after_request
    def after_request(response, db: SQLAlchemy):
        db.session.remove()
        # print("after_request is running")
        return response

    @app.teardown_request
    def teardown_request_func(error, db: SQLAlchemy):
        try:
            db.session.remove()
        except Exception as e:
            app.logger.error(f"Error in teardown_request_func: {e}")
        if error:
            app.logger.error(str(error))

    return github
