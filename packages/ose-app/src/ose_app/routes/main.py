import json
from urllib.parse import quote_plus

from flask import Blueprint, g, render_template, redirect, url_for, request, session, jsonify, current_app
from flask_github import GitHub

from ..injectables import ActiveBranch

from ..guards.with_permission import requires_permissions
from ose.services.ConfigurationService import ConfigurationService

import ose.utils.github as gh

bp = Blueprint("main", __name__, template_folder="../templates")


@bp.route('/')
@bp.route('/home')
@requires_permissions("view")
def home(config: ConfigurationService):
    # Filter just the repositories that the user can see
    user_name = g.user.github_login if g.user else "*"
    user_repos = (config.app_config['USERS']
                  .get(user_name, config.app_config['USERS'].get("*", {}))
                  .get("repositories", []))

    repositories = {s: config.get(s) for s in user_repos}
    repositories = {k: v for k, v in repositories.items() if v is not None}

    if len(repositories) == 1:
        return redirect(url_for("main.repo", repo_key=list(repositories.keys())[0]))

    return render_template('index.html',
                           login=g.user.github_login,
                           repos=repositories)


@bp.route('/repo/<repo_key>')
@bp.route('/repo/<repo_key>/<path:folder_path>')
@requires_permissions("view")
def repo(repo_key, github: GitHub, config: ConfigurationService, active_branch: ActiveBranch, folder_path=""):
    repository = config.get(repo_key)
    # get from ?branch= query parameter
    active_branch = request.args.get('branch', repository.main_branch)
    branches = gh.get_branches(github, repository.full_name)
    params = {"ref": active_branch} if active_branch != repository.main_branch else {}
    directories = github.get(
        f'repos/{repository.full_name}/contents/{folder_path}',
        params=params
    )
    dirs = []
    spreadsheets = []
    for directory in directories:
        if directory['type'] == 'dir':
            dirs.append(directory['name'])
        elif directory['type'] == 'file' and '.xlsx' in directory['name']:
            spreadsheets.append(directory['name'])
    if g.user.github_login in config.app_config['USERS']:
        user_initials = config.app_config['USERS'][g.user.github_login].get("initials", g.user.github_login[0:2])
    else:
        current_app.logger.info(f"The user {g.user.github_login} has no known metadata")
        user_initials = g.user.github_login[0:2]

    breadcrumb_segments = [repo_key, *folder_path.split("/")]

    return render_template('repo.html',
                           login=g.user.github_login,
                           user_initials=user_initials,
                           repo_name=repo_key,
                           branches=branches,
                           active_branch=active_branch,
                           main_branch=repository.main_branch,
                           folder_path=folder_path,
                           breadcrumb=[{"name": s, "path": "repo/" + "/".join(breadcrumb_segments[:i + 1])} for i, s in
                                       enumerate(breadcrumb_segments)],
                           directories=dirs,
                           spreadsheets=spreadsheets,
                           )


@bp.route("/direct", methods=["POST", "GET"])
@requires_permissions("view")
def direct():
    if request.method == "POST":
        typ = json.loads(request.form.get("type"))
        typ = typ["type"]
        repo = json.loads(request.form.get("repo"))
        sheet = json.loads(request.form.get("sheet"))
        go_to_row = json.loads(request.form.get("go_to_row"))
        go_to_row = go_to_row["go_to_row"]
        repo_str = repo['repo']
        sheet_str = sheet['sheet']
    else:
        args = request.args
        typ = args.get("type", None)
        repo_str = args.get("repo", None)
        sheet_str = args.get("sheet", None)
        go_to_row = args.get("go_to_row", None)
        branch = args.get("branch", None)

    if any(x is None for x in [typ, repo_str, sheet_str, go_to_row]):
        return jsonify("invalid number of arguments for get"), 400

    url = '/edit' + '/' + repo_str + '/' + sheet_str + "?filter=" + quote_plus(json.dumps({"Label": go_to_row}))
    if branch:
        url += "&branch=" + quote_plus(branch)

    session['type'] = typ
    session['label'] = go_to_row
    session['url'] = url

    if request.method == "POST":
        return 'success'
    else:
        return redirect(url)
