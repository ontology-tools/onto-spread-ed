from flask import Blueprint, jsonify

bp = Blueprint("api_status", __name__, url_prefix="/status")


@bp.route("/", methods=["GET"])
def status():
    return jsonify({
        "status": "ok",
    })
