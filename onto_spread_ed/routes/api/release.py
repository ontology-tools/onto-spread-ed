import datetime
import os
import tempfile
import threading
from typing import NamedTuple

from flask import jsonify, Blueprint, current_app
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query
from ontoutils import RobotImportsWrapper, RobotTemplateWrapper

from ...database.Release import Release
from ...guards.admin import verify_admin
from ...utils.github import download_file

bp = Blueprint("api_release", __name__, url_prefix="/api/release")


class Repository(NamedTuple):
    full_name: str
    short_name: str
    external: (str, str)
    upper_level_defs: (str, str)
    upper_level_rels: (str, str)
    sub_ontologies: list[(str, str)]


@bp.route("/<repo>", methods=("POST",))
@verify_admin
def release_start(repo: str, db: SQLAlchemy, gh: GitHub):
    q: Query[Release] = Release.query
    ongoing = q.filter_by(running=True).all()
    if len(ongoing) > 0:
        return jsonify(dict(
            error="already-running",
            message="An other release is already running.",
            releases=[r.as_dict() for r in ongoing]
        )), 400

    r = Repository(
        full_name=current_app.config["REPOSITORIES"][repo],
        short_name=repo,
        external=("Upper Level BCIO/inputs/BCIO_External_Imports.xlsx", "Upper Level BCIO/bcio_external.owl"),
        upper_level_defs=("Upper Level BCIO/inputs/BCIO_Upper_Defs.xlsx", "Upper Level BCIO/bcio_upper_level_defs.owl"),
        upper_level_rels=("Upper Level BCIO/inputs/BCIO_Upper_Rel.xlsx", "Upper Level BCIO/bcio_relations.owl"),
        sub_ontologies=[
            ("Setting/inputs/Setting.xlsx", "Setting/bcio_setting.owl"),
            ("ModeOfDelivery/inputs/MoD.xlsx", "ModeOfDelivery/bcio_mode_of_delivery.owl"),
            ("Source/inputs/BCIO_Source.xlsx", "Source/bcio_source.owl"),
            ("MechanismOfAction/inputs/BCIO_MoA.xlsx", "MechanismOfAction/bcio_moa.owl"),
            ("Behaviour/BCIO_behaviour.xlsx", "Behaviour/bcio_behaviour.owl"),
            ("BehaviourChangeTechniques/inputs/BCIO_BehaviourChangeTechniques.xlsx",
             "BehaviourChangeTechniques/bcto.owl"),
            ("StyleOfDelivery/BCIO_StyleOfDelivery.xlsx", "StyleOfDelivery/bcio_style.owl"),
        ]
    )

    release = Release(state="starting", start=datetime.datetime.now(), step=0, current_info={}, running=True)
    db.session.add(release)
    db.session.commit()

    release_thread = threading.Thread(target=do_release, args=(release.id, r, db, gh))
    release_thread.daemon = True
    release_thread.start()

    return jsonify(release.as_dict())


@bp.route("/<id>", methods=("GET",))
@verify_admin
def get_release(id: int):
    q: Query[Release] = Release.query
    release = q.get(id)

    if release is None:
        return jsonify("Not found"), 404

    return jsonify(release.as_dict())


@bp.route("/", methods=("GET",))
@verify_admin
def get_releases():
    q: Query[Release] = Release.query
    releases = q.all()

    if releases is None:
        return jsonify("Not found"), 404

    return jsonify([r.as_dict() for r in releases])


def do_release(release_id: int, repo_details: Repository, db: SQLAlchemy, gh: GitHub):
    q: Query[Release] = db.session.query(Release)
    try:
        update_release(q, release_id, {
            Release.state: "running",
            Release.step: 1
        })

        with tempfile.TemporaryDirectory(f"onto-spread-ed-release-{release_id}") as tmp:
            external_xlsx = os.path.join(tmp, "externals.xlsx")
            upper_level_defs_xlsx = os.path.join(tmp, "upper_level_defs.xlsx")
            upper_level_rels_xlsx = os.path.join(tmp, "upper_level_rels.xlsx")
            sub_ontologies_xlsx = dict(
                (p, os.path.join(tmp, os.path.basename(p[0]))) for p in repo_details.sub_ontologies)

            download_file(gh, repo_details.full_name, repo_details.external[0], external_xlsx)
            download_file(gh, repo_details.full_name, repo_details.upper_level_defs[0], upper_level_defs_xlsx)
            download_file(gh, repo_details.full_name, repo_details.upper_level_rels[0], upper_level_rels_xlsx)
            for f in repo_details.sub_ontologies:
                download_file(gh, repo_details.full_name, f, sub_ontologies_xlsx[f])

            next_release_step(q, release_id)

            external_owl = os.path.join(tmp, 'external.owl')
            upper_rel_csv = os.path.join(tmp, "upper_rel.csv")
            upper_rel_owl = os.path.join(tmp, "upper_rel.owl")

            robot_wrapper = RobotImportsWrapper(robotcmd='robot', cleanup=False)
            robot_wrapper.process_imports_from_excel(
                excel_file=external_xlsx,
                merged_iri='http://humanbehaviourchange.org/ontology/bcio_external.owl',  # TODO: replace with generic
                merged_file=external_owl,
                merged_ontology_name=repo_details.short_name,
                download_path=os.path.join(tmp, "external"))

            next_release_step(q, release_id)

            robot_wrapper = RobotTemplateWrapper(robotcmd='robot')
            robot_wrapper.add_classes_from_excel(upper_level_defs_xlsx)
            robot_wrapper.add_rel_info_from_excel(upper_level_rels_xlsx)
            robot_wrapper.create_csv_relation_template_file(upper_rel_csv)

            BCIO_IRI_PREFIX = 'http://humanbehaviourchange.org/ontology/'  # TODO: replace with generic
            BCIOR_ID_PREFIX = ['\"BCIOR: ' + BCIO_IRI_PREFIX + 'BCIOR_\"']
            ONTOLOGY_IRI = BCIO_IRI_PREFIX + "bcio_relations.owl"

            robot_wrapper.createOntologyFromTemplateFile(
                csvFileName=upper_rel_csv,
                dependency=external_owl,
                iri_prefix=BCIO_IRI_PREFIX,
                id_prefixes=BCIOR_ID_PREFIX,
                ontology_iri=ONTOLOGY_IRI,
                owlFileName=upper_rel_owl)


    except Exception as e:
        update_release(q, release_id, {
            Release.state: "errored",
            Release.running: False,
            Release.end: datetime.datetime.now(),
            Release.current_info: {"error": str(e)},
        })


def update_release(q: Query[Release], release_id: int, patch: dict):
    q.filter(Release.id == release_id).update(patch)


def next_release_step(q: Query[Release], release_id: int):
    update_release(q, release_id, {Release.step: Release.step + 1})
