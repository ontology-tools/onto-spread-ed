from flask import Blueprint, g, current_app, jsonify

from onto_spread_ed.guards.verify_login import verify_logged_in

bp = Blueprint("api_repo", __name__, url_prefix="/api/repo")


@bp.route("/", methods=["GET"])
@verify_logged_in
def get_repos():
    user = current_app.config["USERS_METADATA"].get(g.user.github_login, None)
    if not user:
        return jsonify([])

    repo_keys = user["repositories"]
    repositories = current_app.config["REPOSITORIES"]
    repos = [dict(short=k, full=repositories[k]) for k in repo_keys]

    return jsonify(repos)
