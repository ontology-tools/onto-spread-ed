from flask import Blueprint, g, jsonify

from onto_spread_ed.guards.verify_login import verify_logged_in
from onto_spread_ed.guards.with_permission import requires_permissions
from onto_spread_ed.services.ConfigurationService import ConfigurationService

bp = Blueprint("api_repo", __name__, url_prefix="/api/repo")


@bp.route("/", methods=["GET"])
@requires_permissions("view")
def get_repos(config: ConfigurationService):
    user_name = g.user.github_login if g.user else "*"
    repo_keys = (config.app_config['USERS']
                  .get(user_name, config.app_config['USERS'].get("*", {}))
                  .get("repositories", []))

    repositories = config.loaded_repositories()
    repos = [dict(short=k, full=repositories[k].full_name) for k in repo_keys]

    return jsonify(repos)
