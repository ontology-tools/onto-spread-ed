import os
import io
import functools
import openpyxl
import base64
import json

from flask import Flask, request, g, session, redirect, url_for, render_template
from flask import render_template_string, jsonify
from flask_github import GitHub

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# Create an app instance

app = Flask(__name__)

app.config.from_object('config')
app.config['SECRET_KEY']=os.environ['FLASK_SECRET_KEY']
github = GitHub(app)


# setup sqlalchemy

engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    github_id = Column(Integer)
    github_login = Column(String(255))

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token


def verify_logged_in(fn):
    """
    Decorator used to make sure that the user is logged in
    """

    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # If the user is not logged in, then redirect him to the "logged out" page:
        if not g.user:
            return redirect(url_for("loggedout"))
        return fn(*args, **kwargs)

    return wrapped

# Pages:

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('home')
    if access_token is None:
        return redirect(next_url)

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
        db_session.add(user)

    user.github_access_token = access_token

    # Not necessary to get these details here
    # but it helps humans to identify users easily.
    g.user = user
    github_user = github.get('/user')
    user.github_id = github_user['id']
    user.github_login = github_user['login']

    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is None:
        return github.authorize()
    else:
        return 'Already logged in'


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('loggedout'))


@app.route("/loggedout")
def loggedout():
    """
    Displays the page to be shown to logged out users.
    """
    return render_template("loggedout.html")


@app.route('/user')
@verify_logged_in
def user():
    return jsonify(github.get('/user'))


# Pages for the app
@app.route('/')
@app.route('/home')
@verify_logged_in
def home():
    repositories = app.config['REPOSITORIES']
    return render_template('index.html', login=g.user.github_login, repos=repositories)


@app.route('/repo/<repo_key>')
@app.route('/repo/<repo_key>/<folder_path>')
@verify_logged_in
def repo(repo_key, folder_path=""):
    repositories = app.config['REPOSITORIES']
    repo_detail = repositories[repo_key]
    directories = github.get(
        f'repos/{repo_detail}/contents/{folder_path}'
    )
    #print(directories)
    dirs = []
    spreadsheets = []
    for directory in directories:
        if directory['type']=='dir':
            dirs.append(directory['name'])
        elif directory['type']=='file' and '.xlsx' in directory['name']:
            spreadsheets.append(directory['name'])

    return render_template('repo.html',
                            login=g.user.github_login,
                            repo_name = repo_key,
                            folder_path = folder_path,
                            directories = dirs,
                            spreadsheets = spreadsheets
                            )


@app.route('/edit/<repo_key>/<folder>/<spreadsheet>')
@verify_logged_in
def edit(repo_key, folder, spreadsheet):
    repositories = app.config['REPOSITORIES']
    repo_detail = repositories[repo_key]
    spreadsheet_file = github.get(
        f'repos/{repo_detail}/contents/{folder}/{spreadsheet}'
    )
    base64_bytes = spreadsheet_file['content'].encode('utf-8')
    decoded_data = base64.decodebytes(base64_bytes)
    wb = openpyxl.load_workbook(io.BytesIO(decoded_data))
    sheet = wb.active

    header = [cell.value for cell in sheet[1] if cell.value]
    rows = []
    for row in sheet[2:sheet.max_row]:
        values = {}
        for key, cell in zip(header, row):
            values[key] = cell.value
        if any(values.values()):
            rows.append(values)

    return render_template('edit.html',
                            login=g.user.github_login,
                            repo_name = repo_key,
                            folder = folder,
                            spreadsheet_name=spreadsheet,
                            header=json.dumps(header),
                            rows=json.dumps(rows)
                            )


if __name__ == "__main__":        # on running python app.py
    init_db()
    app.run(debug=app.config["DEBUG"], port=8080)        # run the flask app

