from flask import Blueprint, jsonify, send_from_directory, abort

from ose.services.PluginService import PluginService

bp = Blueprint("api_plugins", __name__, url_prefix="/api/plugins")


@bp.route("/", methods=["GET"])
def get_plugins(plugin_service: PluginService):
    """Get information about all loaded plugins."""
    return jsonify(plugin_service.get_plugins_info())


@bp.route("/<plugin_id>/static/<path:filename>", methods=["GET"])
def get_plugin_static(plugin_service: PluginService, plugin_id: str, filename: str):
    """Serve static files from a plugin's static folder."""
    static_path = plugin_service.get_plugin_static_path(plugin_id)
    
    if static_path is None:
        abort(404, f"Plugin '{plugin_id}' not found or has no static folder")
    
    return send_from_directory(static_path, filename)
