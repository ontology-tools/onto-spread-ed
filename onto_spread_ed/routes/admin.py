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


def release_data(db: SQLAlchemy, gh: GitHub, id: Optional[int] = None) -> dict:
    if id is None:
        current_release = db.session.query(Release).filter_by(running=True).first()
    else:
        current_release = db.session.query(Release).get(id)
        if current_release is None:
            raise NotFound(f"Cannot find release with id '{id}'.")

    selection = {}
    if not current_release or not current_release.included_files:
        spreadsheets = get_spreadsheets(gh, current_app.config["REPOSITORIES"]["BCIO"], "", "Upper Level BCIO/")
        default = current_app.config["ACTIVE_SPREADSHEETS"]["BCIO"]

        selection = sorted([(f, f in default) for f in spreadsheets])

        def to_tree(l: List[Tuple[str, bool]]) -> Dict[str, Union[List[Tuple[str, bool]], Dict]]:
            tree: Dict[str, Union[List[Tuple[str, bool]], Dict]] = {".": []}
            for entry, selected in l:
                parts = entry.split("/")
                subtree = tree
                for part in parts[:-1]:
                    subtree = subtree.setdefault(part, {".": []})
                subtree["."].append((parts[-1], selected))

            return tree

        selection = to_tree(selection)

    return dict(
        selection=selection,
        release=current_release,
        login=g.user.github_login,
    )


@bp.route("/release/core", methods=("GET",))
@bp.route("/release/core/<id>", methods=("GET",))
@verify_admin
def release_body(id: str, db: SQLAlchemy, gh: GitHub):
    step = int(request.args["step"]) if "step" in request.args else None
    if step is not None and (step < -2 or step > 7):
        return jsonify(dict(error=f"Invalid step argument '{step}'. It must be an integer.")), 400

    id = int(id) if id != "" else None

    data = release_data(db, gh, id)
    release = data["release"]
    if step is not None and (release is None or step > release.step):
        return redirect(url_for("admin.release_body", id=id))

    html = render_template("release_core.html", selected_step=step, **data)
    return jsonify(dict(release=None if data["release"] is None else data["release"].as_dict(), html=html))


@bp.route("/release", methods=("GET",))
@bp.route("/release/<id>", methods=("GET",))
@verify_admin
def release(id: Optional[str], db: SQLAlchemy, gh: GitHub):
    step = int(request.args["step"]) if "step" in request.args else None
    if step is not None and (step < -2 or step > 7):
        return jsonify(dict(error=f"Invalid step argument '{step}'. It must be an integer.")), 400

    id = int(id) if id != "" else None
    data = release_data(db, gh, id)
    release = data["release"]
    if step is not None and (release is None or step > release.step):
        return redirect(url_for("admin.release", id=id))

    return render_template("release.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Release", path="admin/release")
                           ],
                           selected_step=step,
                           **data
                           )
