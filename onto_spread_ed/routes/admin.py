from typing import Union

from flask import Blueprint, render_template, g, request, jsonify, current_app
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..database import Release
from ..guards.admin import verify_admin
from ..utils.github import get_spreadsheets

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
def release(db: SQLAlchemy, gh: GitHub):
    current_release = db.session.query(Release).filter_by(running=True).first()

    spreadsheets = get_spreadsheets(gh, current_app.config["REPOSITORIES"]["BCIO"], "", "Upper Level BCIO/")
    default = current_app.config["DEFAULT_RELEASE_FILES"]["BCIO"]

    selection = sorted([(f, f in default) for f in spreadsheets])

    s = {
        ".": [],
        "Behaviour": {
            ".": [
                "BCIO_behaviour.xlsx"
            ],
            "historical": {
                ".": []
            }
        }
    }

    def to_tree(l: list[tuple[str, bool]]) -> dict[str, Union[list[tuple[str, bool]]], dict]:
        tree:dict[str, Union[list[tuple[str, bool]], dict]] = {".": []}
        for entry, selected in l:
            parts = entry.split("/")
            subtree = tree
            for part in parts[:-1]:
                subtree = subtree.setdefault(part, {".": []})
            subtree["."].append((parts[-1], selected))

        return tree



    return render_template("release.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Release", path="admin/release")
                           ],
                           selection=to_tree(selection),
                           release=current_release,
                           login=g.user.github_login, )
