import datetime
import json
import os
import tempfile
import threading
import traceback
from dataclasses import dataclass
from time import sleep
from typing import Tuple, Optional, Dict

import jsonschema
from flask import jsonify, Blueprint, current_app, request, url_for, make_response, Response, g
from flask_executor import Executor
from flask_github import GitHub, GitHubError
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query

from ...database.Release import Release
from ...guards.admin import verify_admin
from ...model.ExcelOntology import ExcelOntology
from ...model.Result import Result
from ...services.RobotOntologyBuildService import RobotOntologyBuildService
from ...utils import github
from ...utils.github import download_file

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


class ReleaseCanceledException(Exception):
    pass


@dataclass
class ReleaseScript:
    iri_prefix: str
    upper_level_iri: str
    external_iri: str
    ontology_annotations: Dict[str, str]
    full_repository_name: str
    short_repository_name: str
    prefixes: Dict[str, str]
    external: Tuple[str, str]
    upper_level: Tuple[str, str]
    upper_level_rels: Optional[str] = None

    @classmethod
    def from_json(cls, json: dict):
        r = ReleaseScript(**json)
        r.external = tuple(r.external)
        r.upper_level = tuple(r.upper_level)
        return r


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


@bp.route("/<repo>/start", methods=("POST",))
@verify_admin
def release_start(repo: str, db: SQLAlchemy, gh: GitHub, executor: Executor):
    q: Query[Release] = db.session.query(Release)
    ongoing = q.filter_by(running=True).all()
    if len(ongoing) > 0:
        return jsonify(dict(
            success=False,
            error="already-running",
            message="An other release is already running.",
            releases=[r.as_dict() for r in ongoing]
        )), 400

    if repo not in current_app.config["REPOSITORIES"]:
        return jsonify(dict(
            success=False,
            error="no-such-repository",
            message=f"No repository '{repo}' found. Possible values are {current_app.config['REPOSITORIES'].keys()}",
        )), 400

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "req_body_release_start.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    release_script = ReleaseScript(
        iri_prefix="http://humanbehaviourchange.org/ontology/",
        external_iri="http://humanbehaviourchange.org/ontology/bcio_external.owl",
        upper_level_iri="http://humanbehaviourchange.org/ontology/bcio_upper.owl",
        ontology_annotations={
            "rdfs:comment": "The Behaviour Change Intervention Ontology (BCIO) is an ontology for all aspects of "
                            "human behaviour change interventions and their evaluation. It is being developed "
                            "as a part of the Human Behaviour Change Project (http://www.humanbehaviourchange.org). "
                            "The BCIO is developed across several modules. This ontology file contains the merged "
                            "version of the BCIO, encompassing the upper level and the modules for Setting, "
                            "Mode of Delivery, Style of Delivery, Source, Mechanisms of Action, Behaviour and "
                            "Behaviour Change Techniques. Additional modules will be added soon.",
            "dc:title": "Behaviour Change Intervention Ontology"
        },
        full_repository_name=current_app.config["REPOSITORIES"][repo],
        short_repository_name=repo,
        prefixes={
            "BCIOR": 'http://humanbehaviourchange.org/ontology/BCIOR_',
            "BCIO": 'http://humanbehaviourchange.org/ontology/BCIO_',
            "ADDICTO": "http://addictovocab.org/ADDICTO_"
        },
        external=("Upper Level BCIO/inputs/BCIO_External_Imports.xlsx", "Upper Level BCIO/bcio_external.owl"),
        upper_level=("Upper Level BCIO/inputs/BCIO_Upper_Defs.xlsx", "Upper Level BCIO/bcio_upper_level.owl"),
        upper_level_rels="Upper Level BCIO/inputs/BCIO_Upper_Rels.xlsx"
    )

    release = Release(state="starting",
                      start=datetime.datetime.utcnow(),
                      step=RELEASE_STEP_PREPARATION,
                      started_by=g.user.github_login,
                      details={},
                      running=True,
                      included_files=data["files"],
                      release_script=release_script.__dict__)
    db.session.add(release)
    db.session.commit()

    executor.submit(do_release, db, gh, release_script, release.id)

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

    if release.step != RELEASE_STEP_HUMAN:
        return jsonify(dict(
            success=False,
            error="cannot-be-continued",
            message="The release cannot be manually continued in its current step."
        )), 400

    next_release_step(q, release.id)

    if release.worker_id is None:
        release_script = ReleaseScript.from_json(release.release_script)

        executor.submit(do_release,  db, gh, release_script, release.id)

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

    if release.worker_id is None:
        release_script = ReleaseScript.from_json(release.release_script)

        executor.submit(do_release, db, gh, release_script, release.id)

    return jsonify(release.as_dict())


@bp.route("/download", methods=("GET",))
@verify_admin
def download_release_file(db: SQLAlchemy):
    q = db.session.query(Release)

    release, err = get_current_release(q)
    if err is not None:
        return err

    if release.step < RELEASE_STEP_HUMAN:
        return jsonify(dict(success=False,
                            error="invalid-step",
                            message="The release does not contain files to download.")), 404

    if "file" not in request.args:
        return jsonify(dict(success=False,
                            error="invalid-query",
                            message="Expected 'file' argument.")), 400

    file = request.args.get("file")
    details = release.details[str(RELEASE_STEP_HUMAN)]
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


def local_name(tmp: str, remote_name: str, file_ending=None) -> str:
    external_xlsx = os.path.join(tmp, os.path.basename(remote_name))

    if file_ending is not None:
        return external_xlsx[:external_xlsx.rfind(".")] + file_ending

    return external_xlsx


def do_release(db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int) -> None:
    q: Query[Release] = db.session.query(Release)

    builder = RobotOntologyBuildService()

    release: Release = q.get(release_id)
    if release.local_dir:
        tmp = release.local_dir
    else:
        tmp_dir = tempfile.mkdtemp(f"onto-spread-ed-release-{release_id}")
        tmp = tmp_dir

    try:
        update_release(q, release_id, {
            Release.state: "running",
            Release.worker_id: f"{os.getpid()}-{threading.current_thread().ident}",
            Release.local_dir: tmp
        })

        # external_xlsx = os.path.join(tmp, "externals.xlsx")
        # upper_level_defs_xlsx = os.path.join(tmp, "upper_level_defs.xlsx")
        # upper_level_rels_xlsx = os.path.join(tmp, "upper_level_rels.xlsx")
        #
        # external_owl = os.path.join(tmp, 'external.owl')
        # upper_rel_csv = os.path.join(tmp, "upper_rel.csv")
        # upper_rel_owl = os.path.join(tmp, "upper_rel.owl")

        def _raise_if_canceled():
            r: Release = q.get(release_id)
            if r.state == "canceled":
                raise ReleaseCanceledException("Release has been canceled!")

        def _local_name(remote_name, file_ending=None) -> str:
            return local_name(tmp, remote_name, file_ending)

        def release_step_preparation():
            external_xlsx = _local_name(release_script.external[0])
            download_file(gh, release_script.full_repository_name, release_script.external[0], external_xlsx)
            _raise_if_canceled()

            upper_level_defs_xlsx = _local_name(release_script.upper_level[0])
            download_file(gh, release_script.full_repository_name, release_script.upper_level[0],
                          upper_level_defs_xlsx)
            _raise_if_canceled()

            if release_script.upper_level_rels is not None:
                upper_level_rels_xlsx = _local_name(release_script.upper_level_rels)
                download_file(gh, release_script.full_repository_name, release_script.upper_level_rels,
                              upper_level_rels_xlsx)
                _raise_if_canceled()

            for f in release.included_files:
                download_file(gh, release_script.full_repository_name, f, _local_name(f))
                _raise_if_canceled()

            next_release_step(q, release_id)

            return True

        def release_step_validation():
            # Validate
            validation_info = dict()
            validation_result = Result(())

            result, upper = _load_upper()
            _raise_if_canceled()
            result += upper.validate()
            _raise_if_canceled()

            validation_info["upper"] = dict(
                valid=result.ok(),
                warnings=result.warnings,
                errors=result.errors
            )
            validation_result += result

            external_xlsx = _local_name(release_script.external[0])
            for excel_file in release.included_files:
                result = Result(())
                local_xlsx = _local_name(excel_file)
                iri = release_script.iri_prefix + os.path.basename(excel_file).replace(".xlsx", ".owl")
                lower = ExcelOntology(iri)

                result += lower.import_other_excel_ontology(upper)
                result += lower.add_imported_terms(release_script.external[0], external_xlsx)

                _raise_if_canceled()

                result += lower.add_terms_from_excel(excel_file, local_xlsx)
                _raise_if_canceled()

                result += lower.resolve()
                _raise_if_canceled()

                result += lower.validate()
                _raise_if_canceled()

                validation_info[excel_file] = dict(
                    valid=result.ok(),
                    warnings=result.warnings,
                    errors=result.errors
                )
                validation_result += result

            set_release_info(q, release_id, validation_info)
            if not validation_result.has_errors() and validation_result.ok():
                next_release_step(q, release_id)
            else:
                update_release(q, release_id, dict(state="waiting-for-user"))

            return result.ok()

        def _load_upper():
            result = Result(())
            upper = ExcelOntology(release_script.upper_level_iri)

            external_xlsx = _local_name(release_script.external[0])
            result += upper.add_imported_terms(release_script.external[0], external_xlsx)

            upper_level_defs_xlsx = _local_name(release_script.upper_level[0])
            result += upper.add_terms_from_excel(release_script.upper_level[0], upper_level_defs_xlsx)

            if release_script.upper_level_rels is not None:
                upper_level_rels_xlsx = _local_name(release_script.upper_level_rels)
                result += upper.add_relations_from_excel(release_script.upper_level_rels, upper_level_rels_xlsx)

            result += upper.resolve()
            return result, upper

        def release_step_import():
            result = Result(())
            ontology = ExcelOntology(release_script.external_iri)

            external_xlsx = _local_name(release_script.external[0])
            result += ontology.add_imported_terms(release_script.external[0], external_xlsx)

            _raise_if_canceled()

            result += builder.merge_imports(
                ontology.imports(),
                _local_name(release_script.external[1]),
                release_script.external_iri,
                release_script.short_repository_name,
                tmp
            )
            _raise_if_canceled()

            set_release_result(q, release_id, result)
            return result.ok()

        def release_step_build_upper():
            result, upper = _load_upper()
            _raise_if_canceled()

            result += builder.build_ontology(
                upper,
                _local_name(release_script.upper_level[1]),
                release_script.prefixes,
                [os.path.basename(release_script.external[1])],
                tmp
            )
            _raise_if_canceled()

            set_release_result(q, release_id, result)
            return result.ok()

        def release_step_build_lower():
            result, upper = _load_upper()
            _raise_if_canceled()

            total = len(release.included_files)
            for index, f in enumerate(release.included_files):
                set_release_info(q, release_id, dict(__progress=(index + 1) / total))
                ontology_name = os.path.basename(f)
                ontology_name = ontology_name[:ontology_name.rfind(".")] + ".owl"
                iri = release_script.iri_prefix + ontology_name

                onto = ExcelOntology(iri)

                external_xlsx = _local_name(release_script.external[0])
                result += onto.add_imported_terms(release_script.external[0], external_xlsx)
                _raise_if_canceled()

                result += onto.import_other_excel_ontology(upper)
                _raise_if_canceled()

                result += onto.add_terms_from_excel(f, _local_name(f))
                result += onto.resolve()
                _raise_if_canceled()

                result += builder.build_ontology(onto, _local_name(f, ".owl"), release_script.prefixes, [
                    os.path.basename(release_script.external[1]),
                    os.path.basename(release_script.upper_level[1])
                ], tmp)
                _raise_if_canceled()

            result.warnings = []
            set_release_result(q, release_id, result)
            return result.ok()

        def release_step_final_merge():
            result = Result(())

            sub_ontologies = [_local_name(f, ".owl") for f in release.included_files]
            ontology_name = release_script.short_repository_name.lower() + ".owl"
            result += builder.merge_ontologies(
                sub_ontologies, _local_name(ontology_name),
                release_script.iri_prefix + ontology_name,
                release_script.iri_prefix + ontology_name + "/" + datetime.datetime.utcnow().strftime("%Y-%m-%d"),
                release_script.ontology_annotations
            )
            _raise_if_canceled()

            set_release_result(q, release_id, result)
            return result.ok()

        def release_step_human_verification():
            sub_ontologies = [r[:r.rfind(".")] + ".owl" for r in release.included_files]
            ontologies = [
                release_script.short_repository_name.lower() + ".owl",
                release_script.upper_level[1],
                *sub_ontologies
            ]
            set_release_info(q, release_id, dict(
                ok=False,
                files=[{"link": url_for(".download_release_file", file=f), "name": f} for f in ontologies]
            ))
            update_release(q, release_id, dict(state="waiting-for-user"))

            return False

        def release_step_publish():
            branch = f"release/{datetime.datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}"
            github.create_branch(gh, release_script.full_repository_name, branch)
            _raise_if_canceled()

            files = release.details[str(RELEASE_STEP_HUMAN)]["files"]
            total = len(files)
            for index, file in enumerate(files):
                set_release_info(q, release_id, dict(__progress=(index + 1) / total))
                with open(_local_name(file["name"]), "rb") as f:
                    content = f.read()
                    github.save_file(gh, release_script.full_repository_name, file["name"], content,
                                     f"Release {file['name']}.", branch)
                sleep(1)  # Wait a second to avoid rate limit
                _raise_if_canceled()

            release_month = datetime.datetime.utcnow().strftime('%B %Y')
            release_body = f"Released the {release_month} version of {release_script.short_repository_name}"
            pr_nr = github.create_pr(gh, release_script.full_repository_name,
                                     title=f"{release_month} Release",
                                     body=release_body,
                                     source=branch,
                                     target="master")
            _raise_if_canceled()

            github.merge_pr(gh, release_script.full_repository_name, pr_nr, "squash")
            _raise_if_canceled()

            return True

        last_step = q.get(release_id).step
        release_steps = [
            release_step_preparation,
            release_step_validation,
            release_step_import,
            release_step_build_upper,
            release_step_build_lower,
            release_step_final_merge,
            release_step_human_verification,
            release_step_publish
        ]

        for i, step in enumerate(release_steps):
            if last_step <= i:
                continu = step()
                if not continu:
                    return

                current_step = q.get(release_id).step
                if current_step <= last_step and i != len(release_steps) - 1:
                    current_app.logger.error("The step did not change after a release step was executed. "
                                             "Did an error occur? Not running further release steps.")
                    return

                last_step = current_step

        update_release(q, release_id, {
            Release.state: "completed",
            Release.end: datetime.datetime.utcnow(),
            Release.running: False
        })

    except ReleaseCanceledException:
        pass
    except GitHubError as e:
        set_release_info(q, release_id, {"error": {
            "short": "GitHub " + str(e),
            "long": f"While communicating with github ({e.response.url}) the error {str(e)} occurred.",
            "url": e.response.url
        }})
        update_release(q, release_id, {Release.state: "errored"})
    except Exception as e:
        set_release_info(q, release_id, {"error": {"short": str(e), "long": traceback.format_exc()}})
        update_release(q, release_id, {Release.state: "errored"})
        current_app.logger.error(traceback.format_exc())
    finally:
        update_release(q, release_id, {Release.worker_id: None})


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


def set_release_info(q: Query[Release], release_id: int, details) -> None:
    r = q.get(release_id)
    update_release(q, release_id, {Release.details: {**r.details, r.step: details}})


def update_release(q: Query[Release], release_id: int, patch: dict) -> None:
    q.filter(Release.id == release_id).update(patch)
    q.session.commit()


def next_release_step(q: Query[Release], release_id: int) -> None:
    return update_release(q, release_id, {Release.step: Release.step + 1})


def set_release_result(q, release_id, result):
    set_release_info(q, release_id, dict(
        errors=result.errors,
        warnings=result.warnings
    ))
    if not result.has_errors() and result.ok():
        next_release_step(q, release_id)
    else:
        update_release(q, release_id, dict(state="waiting-for-user"))
