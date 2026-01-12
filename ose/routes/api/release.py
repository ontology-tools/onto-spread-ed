import dataclasses
import datetime
import json
import os
from typing import Tuple

import jsonschema
from flask import jsonify, Blueprint, current_app, request, make_response, Response, g
from flask_executor import Executor
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query
from werkzeug.exceptions import NotFound, BadRequest

from ose.services.PluginService import PluginService

from ...database.Release import Release, ReleaseArtifact
from ...guards.with_permission import requires_permissions
from ...model.Diff import diff
from ...model.ReleaseScript import ReleaseScript
from ...release.do_release import do_release
from ...release.common import next_release_step
from ...services.ConfigurationService import ConfigurationService
from ...utils import save_file, get_file

bp = Blueprint("api_release", __name__, url_prefix="/api/release")

RELEASE_STEP_SELECTION = -1
RELEASE_STEP_PREPARATION = 0
RELEASE_STEP_VALIDATION = 1
RELEASE_STEP_EXTERNAL = 2
RELEASE_STEP_UPPER = 3
RELEASE_STEP_LOWER = 4
RELEASE_STEP_FINAL = 5
RELEASE_STEP_HUMAN = 6
RELEASE_STEP_PUBLISH = 7


def get_current_release(q: Query[Release], repo: str) -> Release | Tuple[Response, int]:
    ongoing = q.filter_by(running=True, repo=repo).all()
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
    repo_config = config.get(repo)
    if repo_config is None:
        raise NotFound(f"No such repository '{repo}'.")

    # Try get from remote
    data = config.get_file(repo_config, repo_config.release_script_path)
    if data is None:
        raise NotFound(f"No release script for '{repo}'.")

    data = json.loads(data)

    release_script = ReleaseScript.from_json(data)

    if release_script.short_repository_name.lower() != repo.lower():
        raise BadRequest("Release script repository does not match requested repository")

    release_script.full_repository_name = repo_config.full_name

    return jsonify(dataclasses.asdict(release_script))


@bp.route("/<repo>/release_script", methods=["PUT"])
@requires_permissions("release")
def save_release_script(repo: str, config: ConfigurationService, gh: GitHub):
    repo_config = config.get(repo)
    if repo_config is None:
        raise NotFound(f"No such repository '{repo}'.")

    assert current_app.static_folder is not None

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "release_script.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
        assert data is not None
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    release_script = ReleaseScript.from_json(data)
    release_script_binary = json.dumps(dataclasses.asdict(release_script), indent=2).encode()

    old_release_script_binary = get_file(gh, repo_config.full_name, repo_config.release_script_path)
    old_release_script_json = json.loads(old_release_script_binary)
    old_release_script = ReleaseScript.from_json(old_release_script_json)

    diffs = diff(old_release_script, release_script)
    commit_message = (
        "Update release script. "
        + ", ".join(f"Set {d.field} to {d.new}" for d in diffs if d.change_type == "update")
        + ", ".join(f"Added {d.new} to {d.field}" for d in diffs if d.change_type == "add")
        + ", ".join(f"Removed {d.old} from {d.field}" for d in diffs if d.change_type == "remove")
    )

    save_file(
        gh,
        repo_config.full_name,
        repo_config.release_script_path,
        release_script_binary,
        commit_message,
        repo_config.main_branch,
    )

    return jsonify({"success": True})


@bp.route("/<repo>/cancel", methods=("POST",))
@requires_permissions("release")
def release_cancel(repo: str, db: SQLAlchemy):
    q = db.session.query(Release)
    release_or_err = get_current_release(q, repo)
    if isinstance(release_or_err, tuple):
        return release_or_err

    release = release_or_err

    q.filter(Release.id == release.id).update(
        {
            Release.running: False,
            Release.end: datetime.datetime.now(datetime.timezone.utc),
            Release.state: "canceled",
            Release.worker_id: None,
        }
    )
    q.session.commit()

    release = q.get(release.id)
    assert release is not None

    return jsonify(release.as_dict())


@bp.route("/start", methods=("POST",))
@requires_permissions("release")
def release_start(
    db: SQLAlchemy, gh: GitHub, executor: Executor, config: ConfigurationService, plugin_service: PluginService
):
    assert current_app.static_folder is not None

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "release_script.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
        assert data is not None
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    release_script = ReleaseScript.from_json(data)

    q: Query[Release] = db.session.query(Release)
    ongoing = q.filter_by(running=True, repo=release_script.short_repository_name).all()
    if len(ongoing) > 0:
        return jsonify(
            dict(
                success=False,
                error="already-running",
                message="An other release is already running.",
                releases=[r.as_dict() for r in ongoing],
            )
        ), 400

    repo = release_script.short_repository_name
    repo_config = config.get(repo)
    if repo_config is None:
        return jsonify(
            dict(
                success=False,
                error="no-such-repository",
                message=f"No repository '{repo}' found.",
            )
        ), 400

    release = Release(
        state="starting",
        start=datetime.datetime.utcnow(),
        step=0,
        started_by=g.user.github_login,
        details={},
        running=True,
        repo=repo,
        release_script=dataclasses.asdict(release_script),
    )
    db.session.add(release)
    db.session.commit()

    f = executor.submit(do_release, db, gh, release_script, release.id, config, plugin_service)

    return jsonify(release.as_dict())


@bp.route("/<repo>/continue")
@requires_permissions("release")
def release_continue(
    repo: str,
    db: SQLAlchemy,
    gh: GitHub,
    executor: Executor,
    config: ConfigurationService,
    plugin_service: PluginService,
):
    q: Query[Release] = db.session.query(Release)
    force = request.args.get("force", "false").lower() == "true"

    release_or_err = get_current_release(q, repo)
    if isinstance(release_or_err, tuple):
        return release_or_err

    release = release_or_err

    if release.state in ["canceled", "completed"]:
        return jsonify(
            dict(success=False, error="canceled-or-completed", message="Cannot resume a completed or canceled release!")
        ), 400

    if release.state != "waiting-for-user" and not force:
        return jsonify(
            dict(
                success=False,
                error="still-running",
                message="The release is still running. It can only be continued if paused or interrupted.",
            )
        ), 400

    release_script = ReleaseScript.from_json(release.release_script)
    if release_script.steps[release.step].name != "HUMAN_VERIFICATION" and not force:
        return jsonify(
            dict(
                success=False,
                error="cannot-be-continued",
                message="The release cannot be manually continued in its current step.",
            )
        ), 400

    next_release_step(q, release.id)

    if release.worker_id is None:
        f = executor.submit(do_release, db, gh, release_script, release.id, config, plugin_service)

    return jsonify(release.as_dict())


@bp.route("/<repo>/rerun-step", methods=("POST", "GET"))
@requires_permissions("release")
def release_rerun_step(
    repo: str,
    db: SQLAlchemy,
    gh: GitHub,
    executor: Executor,
    config: ConfigurationService,
    plugin_service: PluginService,
):
    q: Query[Release] = db.session.query(Release)
    release_or_err = get_current_release(q, repo)
    if isinstance(release_or_err, tuple):
        return release_or_err

    release = release_or_err

    if release.state in ["canceled", "completed"]:
        return jsonify(
            dict(success=False, error="canceled-or-completed", message="Cannot resume a completed or canceled release!")
        ), 400

    if release.worker_id is None or request.args.get("force", "false").lower() == "true":
        release_script = ReleaseScript.from_json(release.release_script)

        f = executor.submit(do_release, db, gh, release_script, release.id, config, plugin_service)

    return jsonify(release.as_dict())


@bp.route("/download", methods=("GET",))
@requires_permissions("release")
def download_release_file(db: SQLAlchemy):
    file = request.args.get("file", "<none>")
    if not file.isdigit():
        return jsonify(dict(success=False, error="invalid-query", message="Expected 'file' argument.")), 400

    artifact = db.session.get(ReleaseArtifact, int(file))
    if artifact is not None and artifact.downloadable:
        with open(artifact.local_path, "rb") as o:
            response = make_response(o.read())
            if artifact.local_path.endswith(".xlsx"):
                response.headers.set(
                    "Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                response.headers.set("Content-Type", "text/plain")

            response.headers.set("Content-Disposition", "attachment", filename=os.path.basename(artifact.target_path))

            return response

    return jsonify(dict(success=False, error="no-such-file", message=f"No such file '{file}' in the release.")), 404


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
