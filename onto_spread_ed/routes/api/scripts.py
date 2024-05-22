import importlib
import sys
import traceback

from flask import Blueprint, current_app, jsonify, request
from injector import Injector, inject

from onto_spread_ed.guards.admin import verify_admin

bp = Blueprint("api_scripts", __name__, url_prefix="/api/scripts")


@bp.route("/", methods=["GET"])
@verify_admin
def get_all_scripts():
    scripts = current_app.config["SCRIPTS"]
    return jsonify({
        "success": True,
        "result": dict((k, {
            "title": v['title'],
            "arguments": v['arguments']
        }) for k, v in scripts.items())
    })


@bp.route("/<name>/run", methods=["POST"])
@verify_admin
def run_script(injector: Injector, name: str):
    scripts = current_app.config["SCRIPTS"]

    if name not in scripts:
        return jsonify({"success": False, "error": f"No such script '{name}'"}), 400

    script = scripts[name]

    args = request.json.get("args", [])
    if len(script['arguments']) != len(args):
        return jsonify({"success": False, "error": "Wrong number of arguments"}), 400

    try:
        module = importlib.import_module(script["module"])

        if hasattr(module, script["function"]):
            fn = getattr(module, script["function"])

            kwargs = dict((s['name'], a) for s, a in zip(script['arguments'], args))

            result = injector.call_with_injection(callable=inject(fn), kwargs=kwargs)

            return jsonify({
                "success": True,
                "result": result
            })
        else:
            return jsonify({
                "success": False,
                "error": f"No such function '{script['function']}' in '{script['module']}'"
            }), 400
    except Exception:
        error = traceback.format_exc()
        current_app.logger.error(error)
        return jsonify({"success": False, "error": error})
    finally:
        for mod in sys.modules.keys():
            if mod.startswith(f"{script['module']}."):
                del sys.modules[mod]

        del sys.modules[script["module"]]
