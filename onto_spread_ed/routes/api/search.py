from flask import Blueprint, request, jsonify

from onto_spread_ed.SpreadsheetSearcher import SpreadsheetSearcher
from onto_spread_ed.guards.admin import verify_admin

bp = Blueprint("api_search", __name__, url_prefix="/api/search")

@bp.route("/<string:repo>", methods=["GET"])
@verify_admin
def search(repo: str, searcher: SpreadsheetSearcher):
    label = request.args.get("label", None)
    id = request.args.get("id", None)

    results = searcher.search_for(repo, label, fields=["label", "definition"])

    return jsonify(results)

