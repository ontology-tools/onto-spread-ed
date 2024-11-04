from typing import Optional

from flask import Blueprint, render_template, g, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..database.Release import Release
from ..guards.with_permission import requires_permissions
from ..services.ConfigurationService import ConfigurationService

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")


@bp.route("/")
@bp.route("/dashboard")
@requires_permissions(any_of=["hierarchical-spreadsheets", "index", "repository-config-view"])
def dashboard():
    return render_template("dashboard.html",
                           login=g.user.github_login,
                           breadcrumb=[{"name": "Admin", "path": "/admin/dashboard"}])


# Pages for the app
@bp.route("/rebuild-index", methods=("GET", "POST"))
@requires_permissions("index")
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
@requires_permissions("release")
def release(repo: Optional[str], id: Optional[int], db: SQLAlchemy, config: ConfigurationService):
    data = release_data(db, id, repo)

    current_release: Release = data["release"]
    repositories = None

    if id is None and repo is None:
        # Filter just the repositories that the user can see:
        user_name = g.user.github_login if g.user else "*"
        user_repos = (config.app_config['USERS']
                      .get(user_name, config.app_config['USERS'].get("*", {}))
                      .get("repositories", []))

        repositories = {s: config.get(s) for s in user_repos}
        repositories = {k: v for k, v in repositories.items() if v is not None}

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


@bp.route("/settings")
@requires_permissions("repository-config-view")
def settings(config: ConfigurationService):
    return render_template("settings.html",
                           login=g.user.github_login,
                           config=config.app_config,
                           config_service=config,
                           breadcrumb=[{"name": "Admin", "path": "/admin/settings"}])
