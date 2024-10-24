from flask import Blueprint, request, jsonify

from onto_spread_ed.SpreadsheetSearcher import SpreadsheetSearcher
from onto_spread_ed.guards.with_permission import requires_permissions

bp = Blueprint("api_search", __name__, url_prefix="/api/search")


@bp.route("/<string:repo>", methods=["GET"])
@requires_permissions("view")
def search(repo: str, searcher: SpreadsheetSearcher):
    label = request.args.get("label", None)

    results = searcher.search_for(repo, label, fields=["label", "definition"])

    return jsonify(results)
