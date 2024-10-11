from flask import Blueprint, request, jsonify
from flask_github import GitHub

from onto_spread_ed.guards.admin import verify_admin
from onto_spread_ed.services.ConfigurationService import ConfigurationService
from onto_spread_ed.services.RepositoryConfigurationService import RepositoryConfigurationService

bp = Blueprint("api_settings", __name__, url_prefix="/api/settings")


@bp.route("/repositories/possibilities", methods=["GET"])
@verify_admin
def possible_repositories(config: ConfigurationService, gh: GitHub):
    if not isinstance(config, RepositoryConfigurationService):
        return jsonify({"success": False, "message": "Not supported!"}), 400

    response = gh.get("/user/repos", all_pages=True)
    repos = [{"short_name": r["name"], "full_name": r["full_name"]} for r in response]

    return jsonify({"success": True, "repositories": repos})


@bp.route("/repositories/startup", methods=["GET"])
@verify_admin
def startup_repositories(config: ConfigurationService):
    return jsonify(config.loaded_repositories())


@bp.route("/repositories/load", methods=["POST"])
@verify_admin
def load_repository(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": f"Invalid format"}), 400

    repo = config.get_by_full_name(data["full_name"])

    if repo is None:
        return jsonify({"success": False,
                        "error": f"Repository configuration for '{data['full_name']}' not found. Ensure the repository is accessible for you and it contains the configuration."}), 400
    else:
        return jsonify({"success": True, "repo": repo})


@bp.route("/repositories/unload", methods=["POST"])
@verify_admin
def unload_repository(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": f"Invalid format"}), 400

    success = config.unload(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/add_startup", methods=["POST"])
@verify_admin
def add_as_default(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": f"Invalid format"}), 400

    success = config.add_startup_repository(data["full_name"])

    return jsonify({"success": success})


@bp.route("/repositories/remove_startup", methods=["POST"])
@verify_admin
def remove_startup(config: ConfigurationService):
    data = request.json

    if "full_name" not in data or not isinstance(data["full_name"], str):
        return jsonify({"success": False, "error": f"Invalid format"}), 400

    success = config.remove_startup_repository(data["full_name"])

    return jsonify({"success": success})
