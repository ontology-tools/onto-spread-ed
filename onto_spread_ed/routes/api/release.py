import dataclasses
import datetime
import json
import os
from time import sleep
from typing import Tuple, Optional

import jsonschema
from flask import jsonify, Blueprint, current_app, request, make_response, Response, g
from flask_executor import Executor
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query
from werkzeug.exceptions import NotFound, BadRequest

from ...database.Release import Release
from ...guards.admin import verify_admin
from ...model.ReleaseScript import ReleaseScript
from ...release import do_release
from ...release.common import next_release_step, local_name
from ...services.ConfigurationService import ConfigurationService

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


def get_current_release(q: Query[Release], repo: str) -> Tuple[Optional[Release], Optional[Tuple[Response, int]]]:
    ongoing = q.filter_by(running=True, repo=repo).all()
    if len(ongoing) > 1:
        return None, (jsonify(dict(
            success=False,
            error="multiple-running",
            message="Multiple releases are running.",
            releases=[r.as_dict() for r in ongoing]
        )), 400)
    if len(ongoing) < 1:
        return None, (jsonify(dict(
            success=False,
            error="no-release-running",
            message="No releases is running.",
            releases=[r.as_dict() for r in ongoing]
        )), 400)

    return ongoing[0], None


@bp.route("/<repo>/release_script", methods=["GET"])
@verify_admin
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
@verify_admin
def save_release_script(repo: str, config: ConfigurationService):
    repo_config = config.get(repo)
    if repo_config is None:
        raise NotFound(f"No such repository '{repo}'.")

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "release_script.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    release_script = ReleaseScript.from_json(data)

    path = os.path.join(current_app.static_folder, f"{repo.lower()}.release.json")

    with open(path, "w") as f:
        json.dump(dataclasses.asdict(release_script), f, indent=2)

    return jsonify({"success": True})


@bp.route("/<repo>/cancel", methods=("POST",))
@verify_admin
def release_cancel(repo: str, db: SQLAlchemy):
    q = db.session.query(Release)
    release, err = get_current_release(q, repo)
    if err is not None:
        return err

    q.filter(Release.id == release.id).update(dict(
        running=False,
        end=datetime.datetime.utcnow(),
        state="canceled",
        worker_id=None
    ))
    q.session.commit()

    return jsonify(q.get(release.id).as_dict())


@bp.route("/start", methods=("POST",))
@verify_admin
def release_start(db: SQLAlchemy, gh: GitHub, executor: Executor, config: ConfigurationService):
    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "release_script.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    release_script = ReleaseScript.from_json(data)

    q: Query[Release] = db.session.query(Release)
    ongoing = q.filter_by(running=True, repo=release_script.short_repository_name).all()
    if len(ongoing) > 0:
        return jsonify(dict(
            success=False,
            error="already-running",
            message="An other release is already running.",
            releases=[r.as_dict() for r in ongoing]
        )), 400

    repo = release_script.short_repository_name
    repo_config = config.get(repo)
    if repo_config is None:
        return jsonify(dict(
            success=False,
            error="no-such-repository",
            message=f"No repository '{repo}' found.",
        )), 400

    release = Release(state="starting",
                      start=datetime.datetime.utcnow(),
                      step=0,
                      started_by=g.user.github_login,
                      details={},
                      running=True,
                      repo=repo,
                      release_script=dataclasses.asdict(release_script))
    db.session.add(release)
    db.session.commit()

    executor.submit(do_release, db, gh, release_script, release.id, config)

    return jsonify(release.as_dict())


@bp.route("/<repo>/continue")
@verify_admin
def release_continue(repo: str, db: SQLAlchemy, gh: GitHub, executor: Executor, config: ConfigurationService):
    q: Query[Release] = db.session.query(Release)
    force = request.args.get('force', "false").lower() == "true"

    release, err = get_current_release(q, repo)
    if err is not None:
        return err

    if release.state in ["canceled", "completed"]:
        return jsonify(dict(
            success=False,
            error="canceled-or-completed",
            message="Cannot resume a completed or canceled release!"
        )), 400

    if release.state != "waiting-for-user" and not force:
        return jsonify(dict(
            success=False,
            error="still-running",
            message="The release is still running. It can only be continued if paused or interrupted."
        )), 400

    release_script = ReleaseScript.from_json(release.release_script)
    if release_script.steps[release.step].name != "HUMAN_VERIFICATION" and not force:
        return jsonify(dict(
            success=False,
            error="cannot-be-continued",
            message="The release cannot be manually continued in its current step."
        )), 400

    next_release_step(q, release.id)

    if release.worker_id is None:
        executor.submit(do_release, db, gh, release_script, release.id, config)

        sleep(1)

    return jsonify(release.as_dict())


@bp.route("/<repo>/rerun-step", methods=("POST", "GET"))
@verify_admin
def release_rerun_step(repo: str, db: SQLAlchemy, gh: GitHub, executor: Executor, config: ConfigurationService):
    q: Query[Release] = db.session.query(Release)
    release, err = get_current_release(q, repo)
    if err is not None:
        return err

    if release.state in ["canceled", "completed"]:
        return jsonify(dict(
            success=False,
            error="canceled-or-completed",
            message="Cannot resume a completed or canceled release!"
        )), 400

    if release.worker_id is None or request.args.get('force', "false").lower() == "true":
        release_script = ReleaseScript.from_json(release.release_script)

        executor.submit(do_release, db, gh, release_script, release.id, config)

    return jsonify(release.as_dict())


@bp.route("/<repo>/download", methods=("GET",))
@verify_admin
def download_release_file(repo: str, db: SQLAlchemy):
    q = db.session.query(Release)

    release, err = get_current_release(q, repo)
    if err is not None:
        return err

    release_script = ReleaseScript.from_json(release.release_script)
    index = str(next((i for i, s in enumerate(release_script.steps) if s.name == "HUMAN_VERIFICATION")))

    if index not in release.details or 'files' not in release.details[index]:
        return jsonify(dict(success=False,
                            error="invalid-step",
                            message="The release does not contain files to download.")), 404

    if "file" not in request.args:
        return jsonify(dict(success=False,
                            error="invalid-query",
                            message="Expected 'file' argument.")), 400

    file = request.args.get("file")
    details = release.details[index]
    for f in details['files']:
        if f["name"] == file:
            name = local_name(release.local_dir, file, ".owl")
            with open(name, "r") as o:
                response = make_response(o.read())
                response.headers.set("Content-Type", "text/plain")
                response.headers.set('Content-Disposition', 'attachment', filename=os.path.basename(name))

            return response

    return jsonify(dict(success=False,
                        error="no-such-file",
                        message=f"No such file '{file}' in the release.")), 404


@bp.route("/<repo>/running", methods=("POST", "GET"))
@verify_admin
def get_running_release(repo: str, db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    release, _ = get_current_release(q, repo)

    if release is None:
        raise NotFound()

    return jsonify(release.as_dict())


@bp.route("/<int:id>", methods=("GET",))
@verify_admin
def get_release(id: int, db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    release = q.get(id)

    if release is None:
        return jsonify(dict(
            success=False,
            error="not-found",
            message=f"Release with id {id} not found."
        )), 404

    return jsonify(release.as_dict())


@bp.route("/<string:repo>", methods=("GET",))
@verify_admin
def get_releases_for_repo(repo: str, db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    releases = q.filter_by(repo=repo)

    if releases is None:
        return jsonify("Not found"), 404

    return jsonify([r.as_dict() for r in releases])


@bp.route("/", methods=("GET",))
@verify_admin
def get_releases(db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    releases = q.all()

    if releases is None:
        return jsonify("Not found"), 404

    return jsonify([r.as_dict() for r in releases])
