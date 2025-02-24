from flask import Blueprint, request, jsonify
from flask_github import GitHub

from ose.guards.with_permission import requires_permissions
from ose.services.ConfigurationService import ConfigurationService
from ose.services.RepositoryConfigurationService import RepositoryConfigurationService

bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")


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
    return jsonify(config.loaded_repositories())


@bp.route("/repositories/load", methods=["POST"])
@requires_permissions("repository-config-manage-loaded")
def load_repository(config: ConfigurationService):
    data = request.json

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
        return jsonify({"success": True, "repo": repo})


@bp.route("/repositories/unload", methods=["POST"])
@requires_permissions("repository-config-manage-loaded")
def unload_repository(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.loading_new_allowed:
        return jsonify({"success": False, "error": "Changing the loaded repositories is not allowed!"}), 403

    success = config.unload(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/add_startup", methods=["POST"])
@requires_permissions("repository-config-manage-startup")
def add_as_default(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.changing_startup_allowed:
        return jsonify({"success": False, "error": "Changing startup repositories is not allowed!"}), 403

    success = config.add_startup_repository(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/remove_startup", methods=["POST"])
@requires_permissions("repository-config-manage-startup")
def remove_startup(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": "Invalid format"}), 400

    if not config.changing_startup_allowed:
        return jsonify({"success": False, "error": "Changing startup repositories is not allowed!"}), 403

    success = config.remove_startup_repository(data["full_name"])

    return jsonify({"success": success})
