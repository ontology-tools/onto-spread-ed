import base64
import hashlib
import json

import yaml
from flask import Blueprint, request, jsonify
from flask_github import GitHub, GitHubError
from pydantic import ValidationError
from yaml import YAMLError

from ose.building import available_stages
from ose.project import Project

from ose_app.guards.with_permission import requires_permissions
from ose_app.helpers import NOT_AN_OBJECT, json_object
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.services.FileCache import FileCache
from ose_app.services.RepositoryConfigurationService import REPOSITORY_CONFIG_PATH_PROP, RepositoryConfigurationService
from ose_app.utils import save_file
from ose_app.utils.config_file import apply_changes

bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")


def project_revision(project: Project) -> str:
    data = json.dumps(project.model_dump(mode="json"), sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


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
        "revision": project_revision(project),
        "available_stages": sorted(available_stages().keys()),
    })


@bp.route("/repositories/<repo>/project", methods=["PUT"])
@requires_permissions("repository-config-edit")
def save_project(repo: str, config: ConfigurationService, gh: GitHub):
    old_project = config.get(repo)
    if old_project is None:
        return jsonify({"success": False, "error": f"No repository '{repo}' is loaded."}), 404

    if not request.if_match.contains(project_revision(old_project)):
        return jsonify({"success": False, "error": "The configuration changed. Reload it and apply your changes again."}), 409

    try:
        project = Project.model_validate(request.get_json(silent=True))
    except ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid project: {e}"}), 400

    if project.full_repository_name != old_project.full_repository_name:
        return jsonify({"success": False, "error": "The repository of a project cannot be changed."}), 400
    if project.short_name != old_project.short_name:
        return jsonify({"success": False, "error": "The short name of a project cannot be changed."}), 400

    old, new = old_project.model_dump(mode="json"), project.model_dump(mode="json")
    if old == new:
        return jsonify({"success": True, "project": new, "revision": project_revision(project)})

    full_name, branch = old_project.full_repository_name, old_project.main_branch
    config_path = config.app_config[REPOSITORY_CONFIG_PATH_PROP]
    try:
        current = gh.get(f"repos/{full_name}/contents/{config_path}", params={"ref": branch})
        text = base64.b64decode(current["content"]).decode("utf-8")
        document = yaml.safe_load(text)
        on_github = Project.model_validate(document)
    except (GitHubError, YAMLError, ValidationError, UnicodeDecodeError) as e:
        return jsonify({"success": False, "error": f"Could not read the current configuration from GitHub: {e}"}), 502

    if on_github.model_dump(mode="json") != old:
        config.replace(on_github)
        return jsonify({"success": False, "error": "The configuration was changed on GitHub since it was loaded. "
                                                   "Reload the configuration and apply your changes again."}), 409

    fields = ", ".join(key.replace("_", " ") for key in new if old[key] != new[key])
    commit_message = f"Update {project.short_name} project configuration\n\nChange {fields}."
    document = apply_changes(document, old, new)
    content = (json.dumps(document, indent=2, ensure_ascii=False) + "\n" if config_path.endswith(".json") else
               yaml.safe_dump(document, sort_keys=False, allow_unicode=True))

    try:
        save_file(gh, full_name, config_path, content.encode(), commit_message, branch, sha=current["sha"])
    except GitHubError as e:
        if e.response.status_code == 409:
            return jsonify({"success": False, "error": "The configuration was changed on GitHub meanwhile. "
                                                       "Reload the configuration and apply your changes again."}), 409
        raise
    config.replace(project)

    return jsonify({"success": True, "project": new, "revision": project_revision(project)})


@bp.route("/repositories/possibilities", methods=["GET"])
@requires_permissions("repository-config-manage-loaded")
def possible_repositories(config: ConfigurationService, gh: GitHub):
    if not isinstance(config, RepositoryConfigurationService):
        return jsonify({"success": False, "message": "Not supported!"}), 400

    response = gh.get("/user/repos", all_pages=True)
    repos = [{"short_name": r["name"], "full_name": r["full_name"]} for r in response]

    return jsonify({"success": True, "repositories": repos})


@bp.route("/repositories/load", methods=["POST"])
@requires_permissions("repository-config-manage-loaded")
def load_repository(config: ConfigurationService):
    data = json_object()
    if data is None:
        return jsonify(NOT_AN_OBJECT), 400

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
    data = json_object()
    if data is None:
        return jsonify(NOT_AN_OBJECT), 400

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.loading_new_allowed:
        return jsonify({"success": False, "error": "Changing the loaded repositories is not allowed!"}), 403

    success = config.unload(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/add_startup", methods=["POST"])
@requires_permissions("repository-config-manage-startup")
def add_as_default(config: ConfigurationService):
    data = json_object()
    if data is None:
        return jsonify(NOT_AN_OBJECT), 400

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.changing_startup_allowed:
        return jsonify({"success": False, "error": "Changing startup repositories is not allowed!"}), 403

    success = config.add_startup_repository(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/remove_startup", methods=["POST"])
@requires_permissions("repository-config-manage-startup")
def remove_startup(config: ConfigurationService):
    data = json_object()
    if data is None:
        return jsonify(NOT_AN_OBJECT), 400

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
    cache.clear()

    return jsonify({"success": True, "message": "Caches cleared successfully"})
