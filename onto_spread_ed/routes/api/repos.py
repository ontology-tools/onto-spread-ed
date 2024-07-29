from flask import Blueprint, g, jsonify

from onto_spread_ed.guards.verify_login import verify_logged_in
from onto_spread_ed.services.ConfigurationService import ConfigurationService

bp = Blueprint("api_repo", __name__, url_prefix="/api/repo")


@bp.route("/", methods=["GET"])
@verify_logged_in
def get_repos(config: ConfigurationService):
    user = config.app_config["USERS_METADATA"].get(g.user.github_login, None)
    if not user:
        return jsonify([])

    repo_keys = user["repositories"]
    repositories = config.loaded_repositories()
    repos = [dict(short=k, full=repositories[k].full_name) for k in repo_keys]

    return jsonify(repos)
