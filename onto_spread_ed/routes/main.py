import json

from flask import Blueprint, current_app, g, render_template, redirect, url_for, request, session
from flask_github import GitHub

from ..guards.verify_login import verify_logged_in

bp = Blueprint("main", __name__, template_folder="../templates")

@bp.route('/')
@bp.route('/home')
@verify_logged_in
def home():
    repositories = current_app.config['REPOSITORIES']
    user_repos = repositories.keys()
    # Filter just the repositories that the user can see
    if g.user.github_login in current_app.config['USERS_METADATA']:
        user_repos = current_app.config['USERS_METADATA'][g.user.github_login]["repositories"]

    repositories = {k: v for k, v in repositories.items() if k in user_repos}

    return render_template('index.html',
                           login=g.user.github_login,
                           repos=repositories)


@bp.route('/repo/<repo_key>')
@bp.route('/repo/<repo_key>/<path:folder_path>')
@verify_logged_in
def repo(repo_key, github: GitHub, folder_path=""):
    repositories = current_app.config['REPOSITORIES']
    repo_detail = repositories[repo_key]
    directories = github.get(
        f'repos/{repo_detail}/contents/{folder_path}'
    )
    dirs = []
    spreadsheets = []
    # go to edit_external:
    if folder_path == 'imports':
        return redirect(url_for('edit.edit_external', repo_key=repo_key, folder_path=folder_path))
    for directory in directories:
        if directory['type'] == 'dir':
            dirs.append(directory['name'])
        elif directory['type'] == 'file' and '.xlsx' in directory['name']:
            spreadsheets.append(directory['name'])
    if g.user.github_login in current_app.config['USERS_METADATA']:
        user_initials = current_app.config ['USERS_METADATA'][g.user.github_login]["initials"]
    else:
        current_app.logger.info(f"The user {g.user.github_login} has no known metadata")
        user_initials = g.user.github_login[0:2]

    return render_template('repo.html',
                           login=g.user.github_login,
                           user_initials=user_initials,
                           repo_name=repo_key,
                           folder_path=folder_path,
                           directories=dirs,
                           spreadsheets=spreadsheets,
                           )


@bp.route("/direct", methods=["POST"])
@verify_logged_in
def direct():
    type = json.loads(request.form.get("type"))
    repo = json.loads(request.form.get("repo"))
    sheet = json.loads(request.form.get("sheet"))
    go_to_row = json.loads(request.form.get("go_to_row"))
    repoStr = repo['repo']
    sheetStr = sheet['sheet']
    url = '/edit' + '/' + repoStr + '/' + sheetStr
    session['type'] = type['type']
    session['label'] = go_to_row['go_to_row']
    session['url'] = url
    return ('success')

