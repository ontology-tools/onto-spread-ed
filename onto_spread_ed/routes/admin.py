from flask import Blueprint, render_template, g, request, jsonify

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..guards.admin import verify_admin

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")


@bp.route("/")
@bp.route("/dashboard")
@verify_admin
def dashboard():
    return render_template("dashboard.html",
                           login=g.user.github_login,
                           breadcrumb=[{"name": "Admin", "path": "admin/dashboard"}])


# Pages for the app
@bp.route("/rebuild-index", methods=("GET", "POST"))
@verify_admin
def rebuild_index(searcher: SpreadsheetSearcher):
    if request.method == "POST":
        sheets = searcher.rebuild_index()
        return jsonify(sheets)
    elif request.method == "GET":
        return render_template("rebuild_index.html",
                               index_stats=searcher.stats(),
                               breadcrumb=[
                                   dict(name="Admin", path="admin/dashboard"),
                                   dict(name="Rebuild index", path="admin/rebuild-index")
                               ],
                               login=g.user.github_login, )


@bp.route("/release", methods=("GET",))
@verify_admin
def release():
    return render_template("release.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Release", path="admin/release")
                           ],
                           login=g.user.github_login, )
