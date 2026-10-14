import os.path
from os.path import normpath

from flask import Blueprint, jsonify, current_app, request
from flask_github import GitHub, GitHubError

from ose_app.guards.with_permission import requires_permissions
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.helpers import all_initials, repo_tree, user_initials, visible_repositories
from ose_app.utils import save_file
from ose_app.utils.github import get_branches

bp = Blueprint("api_repo", __name__, url_prefix="/api/repo")


@bp.route("/", methods=["GET"])
@requires_permissions("view")
def get_repos(config: ConfigurationService):
    repos = [dict(short=k, full=p.full_repository_name) for k, p in visible_repositories(config).items()]

    return jsonify(repos)


@bp.route("/<repo_key>/tree", methods=["GET"])
@requires_permissions("view")
def get_tree(repo_key: str, gh: GitHub, config: ConfigurationService):
    """Whole tree of a repository branch (what the repository browsing page shows)."""
    if repo_key not in visible_repositories(config):
        return jsonify({"success": False, "error": f"No such repository '{repo_key}'"}), 404

    try:
        tree = repo_tree(gh, config, repo_key, request.args.get("branch"))
    except GitHubError as e:
        if e.response.status_code == 404:
            return jsonify({"success": False, "error": "No such branch or repository"}), 404
        raise
    return jsonify(tree)


@bp.route("/<repo_key>/config", methods=["GET"])
@requires_permissions("view")
def get_config(repo_key: str, gh: GitHub, config: ConfigurationService):
    """Repository configuration and branch info needed by the editor."""
    if repo_key not in visible_repositories(config):
        return jsonify({"success": False, "error": f"No such repository '{repo_key}'"}), 404

    repository = config.get(repo_key)
    return jsonify(dict(
        repo_name=repo_key,
        repository_config=repository.model_dump(mode="json"),
        main_branch=repository.main_branch,
        branches=get_branches(gh, repository.full_repository_name),
        initials=user_initials(config),
        all_initials=all_initials(config),
    ))


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
