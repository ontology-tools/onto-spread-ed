import asyncio
import importlib
import sys
import traceback
from typing import Coroutine

from flask import Blueprint, current_app, jsonify, request
from injector import Injector, inject

from ose_app.guards.with_permission import requires_permissions
from ose.model.Script import Script
from ose.services.ConfigurationService import ConfigurationService
from ose.services.PluginService import PluginService

bp = Blueprint("api_scripts", __name__, url_prefix="/api/scripts")


@bp.route("/", methods=["GET"])
@requires_permissions("scripts")
def get_all_scripts(plugin_service: PluginService):
    scripts = plugin_service.get_scripts()
    return jsonify({"success": True, "result": {s.id: {"title": s.title, "arguments": s.arguments} for s in scripts}})


@bp.route("/<name>/run", methods=["POST"])
@requires_permissions("scripts")
def run_script(plugin_service: PluginService, name: str):
    scripts = plugin_service.get_scripts()
    
    script = next((s for s in scripts if s.id == name), None)

    if script is None:
        return jsonify({"success": False, "error": f"No such script '{name}'"}), 400
    
    if request.json is None or "args" not in request.json:
        return jsonify({"success": False, "error": "No arguments provided"}), 400

    args = request.json.get("args", [])
    if len(script.arguments) != len(args):
        return jsonify({"success": False, "error": "Wrong number of arguments"}), 400

    try:
        kwargs = dict((s.name, a) for s, a in zip(script.arguments, args))

        result = script.run(**kwargs)
        
        if isinstance(result, Coroutine):
            result = asyncio.run(result)

        return jsonify({"success": True, "result": result})
    except Exception:
        error = traceback.format_exc()
        current_app.logger.error(error)
        return jsonify({"success": False, "error": error}), 500