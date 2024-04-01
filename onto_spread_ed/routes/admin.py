from typing import Optional

from flask import Blueprint, render_template, g, request, jsonify, current_app, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..database.Release import Release
from ..guards.admin import verify_admin

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")


@bp.route("/")
@bp.route("/dashboard")
@verify_admin
def dashboard():
    return render_template("dashboard.html",
                           login=g.user.github_login,
                           breadcrumb=[{"name": "Admin", "path": "/admin/dashboard"}])


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


def release_data(db: SQLAlchemy, id: Optional[int] = None, repo: Optional[str] = None) -> dict:
    if id is None:
        if repo is not None:
            current_release = db.session.query(Release).filter_by(running=True, repo=repo).first()
        else:
            current_release = None
    else:
        current_release = db.session.query(Release).get(id)
        if current_release is None:
            raise NotFound(f"Cannot find release with id '{id}'.")

    return dict(
        release=current_release,
        login=g.user.github_login,
    )


@bp.route("/release/", methods=("GET",), defaults={"repo": None, "id": None})
@bp.route("/release/<string:repo>", methods=("GET",), defaults={"id": None})
@bp.route("/release/<int:id>", methods=("GET",), defaults={"repo": None})
@verify_admin
def release(repo: Optional[str], id: Optional[int], db: SQLAlchemy):
    data = release_data(db, id, repo)

    current_release: Release = data["release"]
    repositories = None

    if id is None and repo is None:
        repositories = current_app.config['REPOSITORIES']

        user_repos = repositories.keys()
        # Filter just the repositories that the user can see
        if g.user.github_login in current_app.config['USERS_METADATA']:
            user_repos = current_app.config['USERS_METADATA'][g.user.github_login]["repositories"]

        repositories = {k: v for k, v in repositories.items() if k in user_repos}

        if len(repositories) == 1:
            return redirect(url_for("admin.release", repo=list(repositories.keys())[0]))
    elif id is None and repo is not None:
        if current_release is not None:
            return redirect(url_for("admin.release", id=current_release.id))
    elif id is not None and repo is None:
        if current_release is not None:
            repo = current_release.repo

    paths = [dict(name=repo.upper(), path=f"admin/release/{repo}") if repo is not None else None]

    return render_template("release.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Release", path="admin/release"),
                               *[p for p in paths if p is not None]
                           ],
                           repo=repo,
                           repos=repositories,
                           **data
                           )
