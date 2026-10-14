import yaml
from flask import Blueprint, request, jsonify
from flask_github import GitHub
from pydantic import ValidationError

from ose.building import available_stages
from ose.project import Project

from ose_app.guards.with_permission import requires_permissions
from ose_app.model.Diff import diff
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.services.FileCache import FileCache
from ose_app.services.RepositoryConfigurationService import REPOSITORY_CONFIG_PATH_PROP, RepositoryConfigurationService
from ose_app.utils import save_file

bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")


@bp.route("", methods=["GET"])
@requires_permissions("repository-config-view")
def get_settings(config: ConfigurationService):
    return jsonify({
        "repositories": [p.model_dump(mode="json") for p in config.loaded_repositories()],
        "startup_repositories": config.startup_repositories(),
        "changing_startup_allowed": config.changing_startup_allowed,
        "loading_new_allowed": config.loading_new_allowed,
    })


@bp.route("/repositories/<repo>/project", methods=["GET"])
@requires_permissions("repository-config-view")
def get_project(repo: str, config: ConfigurationService):
    project = config.get(repo)
    if project is None:
        return jsonify({"success": False, "error": f"No repository '{repo}' is loaded."}), 404

    return jsonify({
        "project": project.model_dump(mode="json"),
        "available_stages": sorted(available_stages().keys()),
    })


@bp.route("/repositories/<repo>/project", methods=["PUT"])
@requires_permissions("repository-config-edit")
def save_project(repo: str, config: ConfigurationService, gh: GitHub):
    """Saves the project configuration to the repository and uses it from then on"""
    old_project = config.get(repo)
    if old_project is None:
        return jsonify({"success": False, "error": f"No repository '{repo}' is loaded."}), 404

    try:
        project = Project.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid project: {e}"}), 400

    if project.full_repository_name != old_project.full_repository_name:
        return jsonify({"success": False, "error": "The repository of a project cannot be changed."}), 400

    old, new = old_project.model_dump(mode="json"), project.model_dump(mode="json")
    if old == new:
        return jsonify({"success": True, "project": new})

    changes = [
        f"Set {d.field} to {d.new}" if d.change_type == "update" else
        f"Added {d.field}" if d.change_type == "add" and isinstance(d.new, dict) else
        f"Added {d.new} to {d.field}" if d.change_type == "add" else
        f"Removed {d.field}" if isinstance(d.old, dict) else
        f"Removed {d.old} from {d.field}"
        for d in diff(old, new)
    ]
    commit_message = "Update project configuration\n\n" + "\n".join(f"- {c}" for c in changes)

    save_file(
        gh,
        old_project.full_repository_name,
        config.app_config[REPOSITORY_CONFIG_PATH_PROP],
        yaml.safe_dump(project.model_dump(mode="json", exclude_defaults=True), sort_keys=False).encode(),
        commit_message,
        old_project.main_branch,
    )
    config.replace(project)

    return jsonify({"success": True, "project": new})


@bp.route("/repositories/possibilities", methods=["GET"])
@requires_permissions("repository-config-manage-loaded")
def possible_repositories(config: ConfigurationService, gh: GitHub):
    if not isinstance(config, RepositoryConfigurationService):
        return jsonify({"success": False, "message": "Not supported!"}), 400

    response = gh.get("/user/repos", all_pages=True)
    repos = [{"short_name": r["name"], "full_name": r["full_name"]} for r in response]

    return jsonify({"success": True, "repositories": repos})


@bp.route("/repositories/startup", methods=["GET"])
@requires_permissions("repository-config-view")
def startup_repositories(config: ConfigurationService):
    return jsonify([p.model_dump(mode="json") for p in config.loaded_repositories()])


@bp.route("/repositories/load", methods=["POST"])
@requires_permissions("repository-config-manage-loaded")
def load_repository(config: ConfigurationService):
    data = request.json or {}

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.loading_new_allowed:
        return jsonify({"success": False, "error": "Changing the loaded repositories is not allowed!"}), 403

    repo = config.get_by_full_name(data["full_name"])

    if repo is None:
        return jsonify({"success": False,
                        "error": f"Repository configuration for '{data['full_name']}' not found."
                                 "Ensure the repository is accessible for you and it contains the configuration."}), 400
    else:
        return jsonify({"success": True, "repo": repo.model_dump(mode="json")})


@bp.route("/repositories/unload", methods=["POST"])
@requires_permissions("repository-config-manage-loaded")
def unload_repository(config: ConfigurationService):
    data = request.json or {}

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.loading_new_allowed:
        return jsonify({"success": False, "error": "Changing the loaded repositories is not allowed!"}), 403

    success = config.unload(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/add_startup", methods=["POST"])
@requires_permissions("repository-config-manage-startup")
def add_as_default(config: ConfigurationService):
    data = request.json or {}

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.changing_startup_allowed:
        return jsonify({"success": False, "error": "Changing startup repositories is not allowed!"}), 403

    success = config.add_startup_repository(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/remove_startup", methods=["POST"])
@requires_permissions("repository-config-manage-startup")
def remove_startup(config: ConfigurationService):
    data = request.json or {}

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.changing_startup_allowed:
        return jsonify({"success": False, "error": "Changing startup repositories is not allowed!"}), 403

    success = config.remove_startup_repository(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/reload", methods=["POST"])
@requires_permissions("admin")
def reload_config(config: ConfigurationService):
    config.reload()

    return jsonify({"success": True,
                    "repositories": [p.model_dump(mode="json") for p in config.loaded_repositories()]})


@bp.route("/clear_caches", methods=["POST"])
@requires_permissions("admin")
def clear_caches(cache: FileCache):
    """
    Clears caches for the configuration service.
    """
    cache.clear()

    return jsonify({"success": True, "message": "Caches cleared successfully"})
