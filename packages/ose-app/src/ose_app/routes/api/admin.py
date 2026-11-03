from flask import Blueprint, jsonify

from ose_app.SpreadsheetSearcher import SpreadsheetSearcher
from ose_app.guards.with_permission import requires_permissions

bp = Blueprint("api_admin", __name__, url_prefix="/api/admin")


@bp.route("/index", methods=["GET"])
@requires_permissions("index")
def index_stats(searcher: SpreadsheetSearcher):
    return jsonify(searcher.stats())


@bp.route("/index", methods=["POST"])
@requires_permissions("index")
def rebuild_index(searcher: SpreadsheetSearcher):
    return jsonify(searcher.rebuild_index())
