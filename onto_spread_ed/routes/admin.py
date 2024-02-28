from typing import Union, Optional, List, Tuple, Dict

from flask import Blueprint, render_template, g, request, jsonify, current_app, redirect, url_for
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..database.Release import Release
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


def release_data(db: SQLAlchemy, id: Optional[int] = None) -> dict:
    if id is None:
        current_release = db.session.query(Release).filter_by(running=True).first()
    else:
        current_release = db.session.query(Release).get(id)
        if current_release is None:
            raise NotFound(f"Cannot find release with id '{id}'.")

    return dict(
        release=current_release,
        login=g.user.github_login,
    )

@bp.route("/release", methods=("GET",))
@bp.route("/release/<id>", methods=("GET",))
@verify_admin
def release(id: Optional[str], db: SQLAlchemy, gh: GitHub):
    id = int(id) if id != "" else None
    data = release_data(db, id)

    current_release = data["release"]

    if id is None and current_release is not None:
        return redirect(url_for("admin.release", id=current_release.id))

    return render_template("release.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Release", path="admin/release")
                           ],
                           **data
                           )
