import datetime
import os
from typing import Tuple

from flask import jsonify, Blueprint, request, make_response, Response, g
from flask_executor import Executor
from flask_sqlalchemy import SQLAlchemy
from pydantic import ValidationError
from sqlalchemy.orm import Query
from werkzeug.exceptions import NotFound, BadRequest

from ose.building import available_stages
from ose.project import BuildConfiguration

from ose_app.database.Release import OPEN_STATES, Release
from ...guards.with_permission import requires_permissions
from ose_app.release.runner import load_context, run_release, save_context
from ose_app.release.stages import ReleaseContext
from ose_app.services.ConfigurationService import ConfigurationService

bp = Blueprint("api_release", __name__, url_prefix="/api/release")


def get_current_release(q: Query[Release], repo: str) -> Release | Tuple[Response, int]:
    ongoing = q.filter(Release.repo == repo, Release.state.in_(OPEN_STATES)).all()
    if len(ongoing) > 1:
        return (
            jsonify(
                dict(
                    success=False,
                    error="multiple-running",
                    message="Multiple releases are running.",
                    releases=[r.as_dict() for r in ongoing],
                )
            ),
            400,
        )
    if len(ongoing) < 1:
        return (
            jsonify(
                dict(
                    success=False,
                    error="no-release-running",
                    message="No releases is running.",
                    releases=[r.as_dict() for r in ongoing],
                )
            ),
            400,
        )

    return ongoing[0]


@bp.route("/<repo>/release_script", methods=["GET"])
@requires_permissions("release")
def get_release_script(repo: str, config: ConfigurationService):
    project = config.get(repo)
    if project is None:
        raise NotFound(f"No such repository '{repo}'.")

    if project.short_repository_name.lower() != repo.lower():
        raise BadRequest("Release script repository does not match requested repository")

    return jsonify(project.model_dump(mode="json"))


@bp.route("/<repo>/cancel", methods=("POST",))
@requires_permissions("release")
def release_cancel(repo: str, db: SQLAlchemy):
    q = db.session.query(Release)
    release_or_err = get_current_release(q, repo)
    if isinstance(release_or_err, tuple):
        return release_or_err

    release = release_or_err
    release.state = "cancelled"
    release.context = {**(release.context or {}), "state": "cancelled"}
    if release.worker_id is None:
        release.end = datetime.datetime.now(datetime.timezone.utc)
    # otherwise the worker sets `end` once the release has fully stopped
    db.session.commit()

    return jsonify(release.as_dict())


@bp.route("/start", methods=("POST",))
@requires_permissions("release")
def release_start(db: SQLAlchemy, executor: Executor, config: ConfigurationService):
    data = request.json or {}
    repo = data.get("repo")
    project = config.get(repo) if isinstance(repo, str) else None
    if project is None:
        return jsonify(dict(success=False, error="no-such-repository", message=f"No repository '{repo}' found.")), 400

    requested = data.get("build_configuration")
    try:
        if isinstance(requested, dict):
            build_configuration = BuildConfiguration.model_validate(requested)
        elif isinstance(requested, str):
            build_configuration = project.build_configuration(requested)
        elif project.build_configurations:
            build_configuration = project.build_configurations[0]
        else:
            return jsonify({"success": False, "error": "The project has no build configuration"}), 400
    except (ValidationError, KeyError) as e:
        return jsonify({"success": False, "error": f"Invalid build configuration: {e}"}), 400

    stages = available_stages()
    missing = [s.name for s in build_configuration.stages if s.name not in stages]
    if missing:
        return jsonify({"success": False, "error": f"Unknown build stages: {', '.join(missing)}"}), 400

    q = db.session.query(Release)
    ongoing = q.filter(Release.repo == project.short_name, Release.state.in_(OPEN_STATES)).all()
    if len(ongoing) > 0:
        return jsonify(
            dict(
                success=False,
                error="already-running",
                message="An other release is already running.",
                releases=[r.as_dict() for r in ongoing],
            )
        ), 400

    token = g.user.github_access_token
    context = ReleaseContext(
        project=project,
        build_configuration=build_configuration,
        project_dir=config.local_path(project),
        github_token=token,
    )

    release = Release(
        state=context.state,
        start=datetime.datetime.now(datetime.timezone.utc),
        started_by=g.user.github_login,
        repo=project.short_name,
        context=context.model_dump(mode="json"),
    )
    db.session.add(release)
    db.session.commit()

    executor.submit(run_release, db, release.id, token)

    return jsonify(release.as_dict())


@bp.route("/<repo>/continue")
@requires_permissions("release")
def release_continue(repo: str, db: SQLAlchemy, executor: Executor):
    """Continues a paused release. With `force`, the failed stage of an errored release is skipped."""
    q: Query[Release] = db.session.query(Release)
    force = request.args.get("force", "false").lower() == "true"

    release_or_err = get_current_release(q, repo)
    if isinstance(release_or_err, tuple):
        return release_or_err

    release = release_or_err

    if release.state != "paused" and not force:
        return jsonify(
            dict(
                success=False,
                error="still-running",
                message="The release is still running. It can only be continued if paused or interrupted.",
            )
        ), 400

    token = g.user.github_access_token
    if force and release.state == "errored":
        context = load_context(release, token)
        context.skip_current_stage()
        save_context(db, release.id, context)

    if release.worker_id is None:
        executor.submit(run_release, db, release.id, token)

    return jsonify(release.as_dict())


@bp.route("/<repo>/rerun-step", methods=("POST", "GET"))
@requires_permissions("release")
def release_rerun_step(repo: str, db: SQLAlchemy, executor: Executor):
    q: Query[Release] = db.session.query(Release)
    release_or_err = get_current_release(q, repo)
    if isinstance(release_or_err, tuple):
        return release_or_err

    release = release_or_err

    if release.worker_id is None or request.args.get("force", "false").lower() == "true":
        executor.submit(run_release, db, release.id, g.user.github_access_token)

    return jsonify(release.as_dict())


@bp.route("/download", methods=("GET",))
@requires_permissions("release")
def download_release_file(db: SQLAlchemy):
    release_id, artifact_id = request.args.get("release", "<none>"), request.args.get("artifact")
    if not release_id.isdigit() or not artifact_id:
        return jsonify(dict(
            success=False, error="invalid-query", message="Expected 'release' and 'artifact' arguments."
        )), 400

    release = db.session.get(Release, int(release_id))
    context = load_context(release, g.user.github_access_token) if release is not None and release.context else None
    a = context.artifact(artifact_id) if context is not None else None
    if context is None or a is None:
        return jsonify(dict(success=False, error="no-such-file", message=f"No such file '{artifact_id}' in the release.")), 404

    build_dir = os.path.realpath(context.build_dir)
    file = os.path.realpath(os.path.join(build_dir, a.local_path))
    if os.path.commonpath([build_dir, file]) != build_dir or not os.path.isfile(file):
        return jsonify(dict(success=False, error="no-such-file", message=f"No such file '{artifact_id}' in the release.")), 404

    with open(file, "rb") as o:
        response = make_response(o.read())
    if a.local_path.endswith(".xlsx"):
        response.headers.set("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        response.headers.set("Content-Type", "text/plain")

    response.headers.set("Content-Disposition", "attachment", filename=os.path.basename(a.final_path or a.local_path))

    return response


@bp.route("/<repo>/running", methods=("POST", "GET"))
@requires_permissions("release")
def get_running_release(repo: str, db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    release_or_err = get_current_release(q, repo)

    if isinstance(release_or_err, tuple):
        raise NotFound()

    release = release_or_err

    return jsonify(release.as_dict())


@bp.route("/<int:id>", methods=("GET",))
@requires_permissions("release")
def get_release(id: int, db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    release = q.get(id)

    if release is None:
        return jsonify(dict(success=False, error="not-found", message=f"Release with id {id} not found.")), 404

    return jsonify(release.as_dict())


@bp.route("/<string:repo>", methods=("GET",))
@requires_permissions("release")
def get_releases_for_repo(repo: str, db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    releases = q.filter_by(repo=repo)

    if releases is None:
        return jsonify("Not found"), 404

    return jsonify([r.as_dict() for r in releases])


@bp.route("/", methods=("GET",))
@requires_permissions("release")
def get_releases(db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    releases = q.all()

    if releases is None:
        return jsonify("Not found"), 404

    return jsonify([r.as_dict() for r in releases])
