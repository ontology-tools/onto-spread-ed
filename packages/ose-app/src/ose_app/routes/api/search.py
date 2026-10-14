from flask import Blueprint, request, jsonify

from ose_app.SpreadsheetSearcher import SpreadsheetSearcher
from ose_app.guards.with_permission import requires_permissions

bp = Blueprint("api_search", __name__, url_prefix="/api/search")


@bp.route("/<string:repo>", methods=["GET"])
@requires_permissions("view")
def search(repo: str, searcher: SpreadsheetSearcher):
    query = request.args.get("label", None)
    query = request.args.get("term", query)
    query = request.args.get("query", query)
    limit = request.args.get("limit", None, type=int)

    results = searcher.search_for(repo, query, fields=["label", "definition"], limit=limit)

    return jsonify(results)


@bp.route("/<string:repo>/sheets", methods=["POST"])
@requires_permissions("view")
def search_sheets(repo: str, searcher: SpreadsheetSearcher):
    """Search across all sheets of a repository, either by free text `query` or by assigned user `initials`."""
    data = request.get_json(silent=True) or {}

    if data.get("initials"):
        results = searcher.search_for(repo, assigned_user=data["initials"])
    elif data.get("query") is not None:
        results = searcher.search_for(repo, search_string=data["query"])
    else:
        return jsonify({"success": False, "error": "Either 'query' or 'initials' is required."}), 400

    return jsonify(results)
