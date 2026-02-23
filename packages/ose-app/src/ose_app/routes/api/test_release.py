import dataclasses
import datetime

from flask import jsonify, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy

from ose.database.Release import Release
from ose.model.ReleaseScript import ReleaseScript, ReleaseScriptStep, ReleaseScriptFile, ReleaseScriptSource, ReleaseScriptTarget
from ...guards.with_permission import requires_permissions

bp = Blueprint("api_test_release", __name__, url_prefix="/api/test/release")

TEST_REPO = "__test__"

# A realistic 8-step release script used by all scenarios
_RELEASE_SCRIPT = ReleaseScript(
    iri_prefix="http://example.org/test/",
    short_repository_name=TEST_REPO,
    full_repository_name="test-org/test-repo",
    external=ReleaseScriptFile(
        sources=[ReleaseScriptSource(file="external.xlsx", type="classes")],
        target=ReleaseScriptTarget(file="external.owl", iri="http://example.org/test/external.owl"),
    ),
    files={
        "upper": ReleaseScriptFile(
            sources=[ReleaseScriptSource(file="upper.xlsx", type="classes")],
            target=ReleaseScriptTarget(file="upper.owl", iri="http://example.org/test/upper.owl"),
        ),
        "lower": ReleaseScriptFile(
            sources=[ReleaseScriptSource(file="lower.xlsx", type="classes")],
            target=ReleaseScriptTarget(file="lower.owl", iri="http://example.org/test/lower.owl"),
            needs=["upper"],
        ),
    },
    steps=[
        ReleaseScriptStep(name="PREPARATION"),
        ReleaseScriptStep(name="VALIDATION"),
        ReleaseScriptStep(name="IMPORT_EXTERNAL"),
        ReleaseScriptStep(name="BUILD"),
        ReleaseScriptStep(name="MERGE"),
        ReleaseScriptStep(name="BCIO_SEARCH"),
        ReleaseScriptStep(name="HUMAN_VERIFICATION"),
        ReleaseScriptStep(name="GITHUB_PUBLISH"),
    ],
    prefixes={"BCIO": "http://example.org/bcio/", "ADDICTO": "http://example.org/addicto/"},
)

_RELEASE_SCRIPT_DICT = dataclasses.asdict(_RELEASE_SCRIPT)


def _base_release(state: str, step: int, running: bool, details: dict) -> dict:
    """Return kwargs for creating a Release row."""
    return dict(
        state=state,
        step=step,
        running=running,
        start=datetime.datetime.now(datetime.timezone.utc),
        end=None if running else datetime.datetime.now(datetime.timezone.utc),
        started_by="test-user",
        details=details,
        repo=TEST_REPO,
        release_script=_RELEASE_SCRIPT_DICT,
        worker_id=None,
    )


# ---------------------------------------------------------------------------
# Scenario builders — each returns kwargs for Release(...)
# ---------------------------------------------------------------------------

def _scenario_starting() -> dict:
    return _base_release("starting", 0, True, {})


def _scenario_running_preparation() -> dict:
    return _base_release("running", 0, True, {
        "0": {
            "__progress": {
                "progress": 0.35,
                "position": [3, 8],
                "current_item": "upper.xlsx",
                "message": "Downloading",
            }
        }
    })


def _scenario_running_bcio_search() -> dict:
    # Steps 0-4 completed successfully, step 5 running with progress
    details: dict = {}
    for i in range(5):
        details[str(i)] = {"errors": [], "warnings": []}
    details["5"] = {
        "__progress": {
            "progress": 0.62,
            "position": [31, 50],
            "current_item": "BCIO:012345",
            "message": "Querying API for",
        }
    }
    return _base_release("running", 5, True, details)


def _scenario_waiting_validation_errors() -> dict:
    return _base_release("waiting-for-user", 1, True, {
        "0": {"errors": [], "warnings": []},
        "1": {
            "upper.xlsx": {
                "errors": [
                    {
                        "type": "unknown-parent",
                        "msg": "Parent 'NonExistentTerm' not found.",
                        "term": {"id": "BCIO:000123", "label": "Test Term A", "origin": ["upper.xlsx", 42]},
                    },
                    {
                        "type": "missing-label",
                        "msg": "Term has no label.",
                        "term": {"id": "BCIO:000456", "label": None, "origin": ["upper.xlsx", 88]},
                    },
                ],
                "warnings": [
                    {
                        "type": "incomplete-term",
                        "msg": "Term is missing a definition.",
                        "term": {"id": "BCIO:000789", "label": "Incomplete Term", "origin": ["upper.xlsx", 15]},
                    },
                ],
            },
            "lower.xlsx": {
                "errors": [],
                "warnings": [
                    {
                        "type": "unknown-column",
                        "msg": "Unknown column 'extra_col' in spreadsheet.",
                        "column": "extra_col",
                        "file": "lower.xlsx",
                    },
                ],
            },
        },
    })


def _scenario_waiting_http_errors() -> dict:
    details: dict = {}
    for i in range(5):
        details[str(i)] = {"errors": [], "warnings": []}
    details["5"] = {
        "errors": [
            {
                "type": "http-error",
                "term": "BCIO:000100",
                "status_code": 422,
                "response": {
                    "hydra:title": "An error occurred",
                    "hydra:description": "The input data is misformatted.",
                    "violations": [
                        {"propertyPath": "label", "message": "This value should not be blank."},
                        {"propertyPath": "identifier", "message": "This value is not a valid IRI."},
                    ],
                },
            },
            {
                "type": "http-error",
                "term": "BCIO:000200",
                "status_code": 500,
                "response": {
                    "hydra:title": "Internal Server Error",
                    "hydra:description": "An unexpected error occurred on the remote API.",
                },
            },
        ],
        "warnings": [],
    }
    return _base_release("waiting-for-user", 5, True, details)


def _scenario_waiting_technical_errors() -> dict:
    details: dict = {}
    for i in range(3):
        details[str(i)] = {"errors": [], "warnings": []}
    details["3"] = {
        "errors": [
            {
                "command": "robot merge --input upper.owl --input lower.owl --output merged.owl",
                "code": 1,
                "out": "ROBOT merge starting...\nProcessing upper.owl\n",
                "err": "ERROR: Could not find entity 'http://example.org/test/NonExistent'\n"
                       "org.semanticweb.owlapi.model.OWLOntologyCreationException: Parse error\n"
                       "  at org.obolibrary.robot.MergeOperation.merge(MergeOperation.java:108)",
            },
        ],
        "warnings": [],
    }
    return _base_release("waiting-for-user", 3, True, details)


def _scenario_errored() -> dict:
    details: dict = {}
    for i in range(2):
        details[str(i)] = {"errors": [], "warnings": []}
    details["2"] = {
        "error": {
            "short": "ImportError",
            "long": (
                "Traceback (most recent call last):\n"
                '  File "/app/ose/release/do_release.py", line 42, in do_release\n'
                "    step.run(context)\n"
                '  File "/app/ose/release/steps/import_external.py", line 28, in run\n'
                "    owl = download_owl(url)\n"
                '  File "/app/ose/release/steps/import_external.py", line 15, in download_owl\n'
                "    raise ConnectionError(f\"Failed to download {url}: status {resp.status_code}\")\n"
                "ConnectionError: Failed to download http://purl.obolibrary.org/obo/bfo.owl: status 503"
            ),
        },
    }
    return _base_release("errored", 2, False, details)


def _scenario_completed() -> dict:
    details: dict = {}
    for i in range(8):
        details[str(i)] = {"errors": [], "warnings": []}
    release_kwargs = _base_release("completed", 8, False, details)
    release_kwargs["end"] = datetime.datetime.now(datetime.timezone.utc)
    return release_kwargs


def _scenario_canceled() -> dict:
    details: dict = {}
    for i in range(3):
        details[str(i)] = {"errors": [], "warnings": []}
    release_kwargs = _base_release("canceled", 3, False, details)
    release_kwargs["end"] = datetime.datetime.now(datetime.timezone.utc)
    return release_kwargs


SCENARIOS = {
    "starting": {
        "title": "Starting",
        "description": "Just created, no details yet. Shows spinner.",
        "builder": _scenario_starting,
    },
    "running-preparation": {
        "title": "Running (Preparation)",
        "description": "Preparation step with animated download progress bar.",
        "builder": _scenario_running_preparation,
    },
    "running-bcio-search": {
        "title": "Running (BCIO Search)",
        "description": "BCIO Search step with animated API progress bar.",
        "builder": _scenario_running_bcio_search,
    },
    "waiting-validation-errors": {
        "title": "Waiting: Validation Errors",
        "description": "Validation step with diagnostic errors and warnings.",
        "builder": _scenario_waiting_validation_errors,
    },
    "waiting-http-errors": {
        "title": "Waiting: HTTP Errors",
        "description": "BCIO Search step with Hydra API errors (422 + violations).",
        "builder": _scenario_waiting_http_errors,
    },
    "waiting-technical-errors": {
        "title": "Waiting: Technical Errors",
        "description": "Build step with command execution error (code/stdout/stderr).",
        "builder": _scenario_waiting_technical_errors,
    },
    "errored": {
        "title": "Errored",
        "description": "Unhandled exception during import. Shows error banner.",
        "builder": _scenario_errored,
    },
    "completed": {
        "title": "Completed",
        "description": "All 8 steps finished successfully. Shows green checkmarks.",
        "builder": _scenario_completed,
    },
    "canceled": {
        "title": "Canceled",
        "description": "User canceled during build. Shows canceled state.",
        "builder": _scenario_canceled,
    },
}


@bp.before_request
def _debug_only():
    if not current_app.debug:
        return jsonify({"error": "Test endpoints are only available in debug mode."}), 404


@bp.route("/scenarios", methods=["GET"])
@requires_permissions("release")
def list_scenarios():
    return jsonify({
        k: {"title": v["title"], "description": v["description"]}
        for k, v in SCENARIOS.items()
    })


@bp.route("/create/<scenario>", methods=["POST"])
@requires_permissions("release")
def create_scenario(scenario: str, db: SQLAlchemy):
    if scenario not in SCENARIOS:
        return jsonify({"error": f"Unknown scenario '{scenario}'."}), 400

    kwargs = SCENARIOS[scenario]["builder"]()
    release = Release(**kwargs)
    db.session.add(release)
    db.session.commit()

    return jsonify(release.as_dict())


@bp.route("/cleanup", methods=["DELETE"])
@requires_permissions("release")
def cleanup(db: SQLAlchemy):
    count = db.session.query(Release).filter_by(repo=TEST_REPO).delete()
    db.session.commit()
    return jsonify({"deleted": count})
