import json
import os.path
from os.path import normpath

from flask import Blueprint, g, jsonify, current_app
from flask_github import GitHub

from ose_app.guards.with_permission import requires_permissions
from ose_core.model.ReleaseScript import ReleaseScript
from ose_core.services.ConfigurationService import ConfigurationService
from ose_core.utils import save_file

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


@bp.route("/<repo>/install_workflow/<name>", methods=["POST"])
@requires_permissions("admin")
def install_workflow(gh: GitHub, config: ConfigurationService, repo: str, name: str):
    repo = config.get(repo)
    if not repo:
        return jsonify({"msg": f"No such repository '{repo}'", "success": False}), 404

    release_script_json = config.get_file(repo, repo.release_script_path)
    if not release_script_json:
        return jsonify({"msg": f"No release script found in '{repo}'", "success": False}), 404

    release_script = ReleaseScript.from_json(json.loads(release_script_json))

    name = normpath(name).split("/")[-1]
    filepath = f"{current_app.static_folder}/workflows/{name}.yaml.jinja2"
    if not os.path.exists(filepath):
        return jsonify({"msg": f"No such workflow '{name}'", "success": False}), 404

    with open(filepath, "r") as f:
        template = f.read()
        rendered = current_app.jinja_env.from_string(template).render(release_script=release_script)

        save_file(gh, repo.full_name, f".github/workflows/{name}.yaml", rendered.encode("utf-8"),
                  f"Add {name} workflow", repo.main_branch)

    return jsonify({"msg": f"Workflow '{name}' installed", "success": True})
