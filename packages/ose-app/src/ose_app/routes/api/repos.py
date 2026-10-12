import os.path
from os.path import normpath

from flask import Blueprint, g, jsonify, current_app
from flask_github import GitHub

from ose_app.guards.with_permission import requires_permissions
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.utils import save_file

bp = Blueprint("api_repo", __name__, url_prefix="/api/repo")


@bp.route("/", methods=["GET"])
@requires_permissions("view")
def get_repos(config: ConfigurationService):
    user_name = g.user.github_login if g.user else "*"
    repo_keys = (config.app_config['USERS']
                 .get(user_name, config.app_config['USERS'].get("*", {}))
                 .get("repositories", []))

    repos = [dict(short=k, full=p.full_repository_name) for k in repo_keys if (p := config.get(k)) is not None]

    return jsonify(repos)


@bp.route("/<repo>/install_workflow/<name>", methods=["POST"])
@requires_permissions("admin")
def install_workflow(gh: GitHub, config: ConfigurationService, repo: str, name: str):
    project = config.get(repo)
    if project is None:
        return jsonify({"msg": f"No such repository '{repo}'", "success": False}), 404

    name = normpath(name).split("/")[-1]
    filepath = f"{current_app.static_folder}/workflows/{name}.yaml.jinja2"
    if not os.path.exists(filepath):
        return jsonify({"msg": f"No such workflow '{name}'", "success": False}), 404

    with open(filepath, "r") as f:
        template = f.read()
        rendered = current_app.jinja_env.from_string(template).render(release_script=project)

        save_file(gh, project.full_repository_name, f".github/workflows/{name}.yaml", rendered.encode("utf-8"),
                  f"Add {name} workflow", project.main_branch)

    return jsonify({"msg": f"Workflow '{name}' installed", "success": True})
