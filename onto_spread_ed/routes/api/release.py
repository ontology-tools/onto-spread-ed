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
from werkzeug.exceptions import NotFound

from ...database.Release import Release
from ...guards.admin import verify_admin
from ...model.ReleaseScript import ReleaseScript
from ...release import do_release
from ...release.common import next_release_step, local_name

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


def get_current_release(q: Query[Release]) -> Tuple[Optional[Release], Optional[Tuple[Response, int]]]:
    ongoing = q.filter_by(running=True).all()
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


@bp.route("/<repo>/release_script")
@verify_admin
def get_release_script(repo: str):
    if repo not in current_app.config["REPOSITORIES"]:
        raise NotFound(f"No such repository '{repo}'.")

    path = os.path.join(current_app.static_folder, f"{repo.lower()}.release.json")
    if not os.path.exists(path):
        raise NotFound(f"No release script for '{repo}'.")

    with open(path, "r") as f:
        data = json.load(f)

    release_script = ReleaseScript.from_json(data)

    return jsonify(dataclasses.asdict(release_script))


@bp.route("/cancel", methods=("POST",))
@verify_admin
def release_cancel(db: SQLAlchemy):
    q = db.session.query(Release)
    release, err = get_current_release(q)
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
def release_start(db: SQLAlchemy, gh: GitHub, executor: Executor):
    q: Query[Release] = db.session.query(Release)
    ongoing = q.filter_by(running=True).all()
    if len(ongoing) > 0:
        return jsonify(dict(
            success=False,
            error="already-running",
            message="An other release is already running.",
            releases=[r.as_dict() for r in ongoing]
        )), 400

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "release_script.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    release_script = ReleaseScript.from_json(data)

    repo = release_script.short_repository_name
    if repo not in current_app.config["REPOSITORIES"]:
        return jsonify(dict(
            success=False,
            error="no-such-repository",
            message=f"No repository '{repo}' found. Possible values are {current_app.config['REPOSITORIES'].keys()}",
        )), 400

    release = Release(state="starting",
                      start=datetime.datetime.utcnow(),
                      step=RELEASE_STEP_PREPARATION,
                      started_by=g.user.github_login,
                      details={},
                      running=True,
                      included_files=data["files"],
                      release_script=dataclasses.asdict(release_script))
    db.session.add(release)
    db.session.commit()

    executor.submit(do_release, db, gh, release_script, release.id, current_app.config)

    return jsonify(release.as_dict())


@bp.route("/continue")
@verify_admin
def release_continue(db: SQLAlchemy, gh: GitHub, executor: Executor):
    q: Query[Release] = db.session.query(Release)

    release, err = get_current_release(q)
    if err is not None:
        return err

    if release.state in ["canceled", "completed"]:
        return jsonify(dict(
            success=False,
            error="canceled-or-completed",
            message="Cannot resume a completed or canceled release!"
        )), 400

    if release.state != "waiting-for-user":
        return jsonify(dict(
            success=False,
            error="still-running",
            message="The release is still running. It can only be continued if paused or interrupted."
        )), 400

    release_script = ReleaseScript.from_json(release.release_script)
    if release_script.steps[release.step].name != "HUMAN_VERIFICATION":
        return jsonify(dict(
            success=False,
            error="cannot-be-continued",
            message="The release cannot be manually continued in its current step."
        )), 400

    next_release_step(q, release.id)

    if release.worker_id is None:
        executor.submit(do_release, db, gh, release_script, release.id, current_app.config)

        sleep(1)

    return jsonify(release.as_dict())


@bp.route("/rerun-step", methods=("POST", "GET"))
@verify_admin
def release_rerun_step(db: SQLAlchemy, gh: GitHub, executor: Executor):
    q: Query[Release] = db.session.query(Release)
    release, err = get_current_release(q)
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

        executor.submit(do_release, db, gh, release_script, release.id, current_app.config)

    return jsonify(release.as_dict())


@bp.route("/download", methods=("GET",))
@verify_admin
def download_release_file(db: SQLAlchemy):
    q = db.session.query(Release)

    release, err = get_current_release(q)
    if err is not None:
        return err

    release_script = ReleaseScript.from_json(release.release_script)
    index = str(next((i for i, s in enumerate(release_script.steps) if s.name == "HUMAN_VERIFICATION")))

    if index not in release.details or 'files' not in release.details[str(release.step)]:
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


# def do_release(db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int) -> None:
#     q: Query[Release] = db.session.query(Release)
#
#     builder = RobotOntologyBuildService()
#
#     release: Release = q.get(release_id)
#     if release.local_dir:
#         tmp = release.local_dir
#     else:
#         tmp_dir = tempfile.mkdtemp(f"onto-spread-ed-release-{release_id}")
#         tmp = tmp_dir
#
#     try:
#         update_release(q, release_id, {
#             Release.state: "running",
#             Release.worker_id: f"{os.getpid()}-{threading.current_thread().ident}",
#             Release.local_dir: tmp
#         })
#
#         # external_xlsx = os.path.join(tmp, "externals.xlsx")
#         # upper_level_defs_xlsx = os.path.join(tmp, "upper_level_defs.xlsx")
#         # upper_level_rels_xlsx = os.path.join(tmp, "upper_level_rels.xlsx")
#         #
#         # external_owl = os.path.join(tmp, 'external.owl')
#         # upper_rel_csv = os.path.join(tmp, "upper_rel.csv")
#         # upper_rel_owl = os.path.join(tmp, "upper_rel.owl")
#
#         def _raise_if_canceled():
#             r: Release = q.get(release_id)
#             if r.state == "canceled":
#                 raise ReleaseCanceledException("Release has been canceled!")
#
#         def _local_name(remote_name, file_ending=None) -> str:
#             return local_name(tmp, remote_name, file_ending)
#
#         def release_step_preparation():
#             pass
#
#         def release_step_validation():
#             pass
#
#         # def _load_upper():
#         #     result = Result(())
#         #     upper = ExcelOntology(release_script.upper_level_iri)
#         #
#         #     external_xlsx = _local_name(release_script.external[0])
#         #     result += upper.add_imported_terms(release_script.external[0], external_xlsx)
#         #
#         #     upper_level_defs_xlsx = _local_name(release_script.upper_level[0])
#         #     result += upper.add_terms_from_excel(release_script.upper_level[0], upper_level_defs_xlsx)
#         #
#         #     if release_script.upper_level_rels is not None:
#         #         upper_level_rels_xlsx = _local_name(release_script.upper_level_rels)
#         #         result += upper.add_relations_from_excel(release_script.upper_level_rels, upper_level_rels_xlsx)
#         #
#         #     result += upper.resolve()
#         #     return result, upper
#
#         def release_step_import():
#             pass
#
#         def release_step_build_upper():
#             pass
#             # result, upper = _load_upper()
#             # _raise_if_canceled()
#             #
#             # result += builder.build_ontology(
#             #     upper,
#             #     _local_name(release_script.upper_level[1]),
#             #     release_script.prefixes,
#             #     [os.path.basename(release_script.external[1])],
#             #     tmp
#             # )
#             # _raise_if_canceled()
#             #
#             # set_release_result(q, release_id, result)
#             # return result.ok()
#
#         def release_step_build_lower():
#             pass
#             # result, upper = _load_upper()
#             # _raise_if_canceled()
#             #
#             # total = len(release.included_files)
#             # for index, f in enumerate(release.included_files):
#             #     set_release_info(q, release_id, dict(__progress=(index + 1) / total))
#             #     ontology_name = os.path.basename(f)
#             #     ontology_name = ontology_name[:ontology_name.rfind(".")] + ".owl"
#             #     iri = release_script.iri_prefix + ontology_name
#             #
#             #     onto = ExcelOntology(iri)
#             #
#             #     external_xlsx = _local_name(release_script.external[0])
#             #     result += onto.add_imported_terms(release_script.external[0], external_xlsx)
#             #     _raise_if_canceled()
#             #
#             #     result += onto.import_other_excel_ontology(upper)
#             #     _raise_if_canceled()
#             #
#             #     result += onto.add_terms_from_excel(f, _local_name(f))
#             #     result += onto.resolve()
#             #     _raise_if_canceled()
#             #
#             #     result += builder.build_ontology(onto, _local_name(f, ".owl"), release_script.prefixes, [
#             #         os.path.basename(release_script.external[1]),
#             #         os.path.basename(release_script.upper_level[1])
#             #     ], tmp)
#             #     _raise_if_canceled()
#             #
#             # result.warnings = []
#             # set_release_result(q, release_id, result)
#             # return result.ok()
#
#         def release_step_final_merge():
#             pass
#
#         def release_step_human_verification():
#             pass
#
#         def release_step_publish():
#             pass
#
#         last_step = q.get(release_id).step
#         release_steps = [
#             release_step_preparation,
#             release_step_validation,
#             release_step_import,
#             release_step_build_upper,
#             release_step_build_lower,
#             release_step_final_merge,
#             release_step_human_verification,
#             release_step_publish
#         ]
#
#         for i, step in enumerate(release_steps):
#             if last_step <= i:
#                 continu = step()
#                 if not continu:
#                     return
#
#                 current_step = q.get(release_id).step
#                 if current_step <= last_step and i != len(release_steps) - 1:
#                     current_app.logger.error("The step did not change after a release step was executed. "
#                                              "Did an error occur? Not running further release steps.")
#                     return
#
#                 last_step = current_step
#
#         update_release(q, release_id, {
#             Release.state: "completed",
#             Release.end: datetime.datetime.utcnow(),
#             Release.running: False
#         })
#
#     except ReleaseCanceledException:
#         pass
#     except GitHubError as e:
#         set_release_info(q, release_id, {"error": {
#             "short": "GitHub " + str(e),
#             "long": f"While communicating with github ({e.response.url}) the error {str(e)} occurred.",
#             "url": e.response.url
#         }})
#         update_release(q, release_id, {Release.state: "errored"})
#     except Exception as e:
#         set_release_info(q, release_id, {"error": {"short": str(e), "long": traceback.format_exc()}})
#         update_release(q, release_id, {Release.state: "errored"})
#         current_app.logger.error(traceback.format_exc())
#     finally:
#         update_release(q, release_id, {Release.worker_id: None})


@bp.route("/running", methods=("POST", "GET"))
@verify_admin
def get_running_release(db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    release, _ = get_current_release(q)

    if release is None:
        raise NotFound()

    return jsonify(release.as_dict())


@bp.route("/<id>", methods=("GET",))
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



@bp.route("/", methods=("GET",))
@verify_admin
def get_releases(db: SQLAlchemy):
    q: Query[Release] = db.session.query(Release)
    releases = q.all()

    if releases is None:
        return jsonify("Not found"), 404

    return jsonify([r.as_dict() for r in releases])
