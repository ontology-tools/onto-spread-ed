import os

import pytest
from pydantic import ValidationError

from helpers import project_data
from ose.project import Project, ProjectFileSource
from ose.result import Err, Log, Success
from ose.schema import DEFAULT_SCHEMA, ColumnMappingKind


def make_context(stages=("A", "B")):
    # Imported here so the Project tests do not depend on the building package
    from ose.building.BuildContext import BuildContext

    project = Project.model_validate(
        project_data(build_configurations=[{"name": "default", "stages": [{"name": s} for s in stages]}])
    )
    return BuildContext(
        project_dir=".",
        build_dir="build",
        project=project,
        state="starting",
        build_configuration=project.build_configurations[0],
    )


# --- Project ------------------------------------------------------------------


def test_project_expands_shorthands():
    project = Project.model_validate(project_data())

    assert project.external.target.file == "external.owl"
    assert project.external.target.iri == "http://example.org/external.owl"
    assert project.files["lower"].target.iri == "http://example.org/lower.owl"
    source = project.files["upper"].sources[0]
    assert (source.file, source.type, source.spreadsheet_schema) == ("upper.xlsx", "classes", "default")
    assert ProjectFileSource.model_validate("import.owl").type == "owl"


def test_project_keeps_explicit_targets():
    data = project_data()
    data["files"]["upper"]["target"] = {"file": "u.owl", "iri": "http://other.org/u.owl", "publish": False}

    target = Project.model_validate(data).files["upper"].target

    assert (target.file, target.iri, target.publish) == ("u.owl", "http://other.org/u.owl", False)


def test_project_rejects_unknown_needs():
    data = project_data()
    data["files"]["lower"]["needs"] = ["missing"]

    with pytest.raises(ValidationError, match="'lower' needs the unknown file 'missing'"):
        Project.model_validate(data)


def test_project_rejects_cyclic_needs():
    data = project_data()
    data["files"]["upper"]["needs"] = ["lower"]

    with pytest.raises(ValidationError, match="Cyclic dependency"):
        Project.model_validate(data)


def test_project_rejects_unknown_spreadsheet_schema():
    data = project_data()
    data["files"]["upper"]["sources"] = [{"file": "upper.xlsx", "type": "classes", "spreadsheet_schema": "custom"}]

    with pytest.raises(ValidationError, match="unknown spreadsheet schema 'custom'"):
        Project.model_validate(data)


def test_project_round_trips_through_json():
    project = Project.model_validate(project_data(spreadsheet_schemas={"custom": CUSTOM_SCHEMA}))
    assert Project.model_validate_json(project.model_dump_json()) == project


# --- Spreadsheet schemas ------------------------------------------------------

CUSTOM_SCHEMA = {"extends": "default", "mappings": [{"type": "label", "columns": ["Term name"]}]}


def test_project_uses_builtin_schemas_by_default():
    project = Project.model_validate(project_data())

    assert project.spreadsheet_schemas == {}
    assert project.spreadsheet_schema("default") is DEFAULT_SCHEMA
    assert project.spreadsheet_schema("import") is not None
    assert project.spreadsheet_schema("nope") is None


def test_project_defines_spreadsheet_schemas_in_json():
    data = project_data(spreadsheet_schemas={"custom": CUSTOM_SCHEMA})
    data["files"]["upper"]["sources"] = [{"file": "upper.xlsx", "type": "classes", "spreadsheet_schema": "custom"}]

    schema = Project.model_validate(data).spreadsheet_schema("custom")

    assert schema is not None
    assert schema.get_mapping("f", "Term name").get_kind() == ColumnMappingKind.LABEL  # type: ignore[union-attr]
    assert schema.get_mapping("f", "Definition") is not None  # inherited from "default"


def test_project_can_replace_builtin_schema():
    project = Project.model_validate(
        project_data(spreadsheet_schemas={"default": {"mappings": [{"type": "label", "columns": ["Term name"]}]}})
    )

    schema = project.spreadsheet_schema("default")

    assert schema is not None and schema is not DEFAULT_SCHEMA
    assert schema.get_mapping("f", "Definition") is None


@pytest.mark.parametrize(
    "schemas,error",
    [
        ({"custom": {"extends": "missing"}}, "Unknown spreadsheet schema 'missing'"),
        ({"a": {"extends": "b"}, "b": {"extends": "a"}}, "Cyclic spreadsheet schema inheritance"),
        ({"custom": {"mappings": [{"type": "label"}]}}, "needs `columns` or a `pattern`"),
    ],
)
def test_project_rejects_invalid_spreadsheet_schemas(schemas, error):
    with pytest.raises(ValidationError, match=error):
        Project.model_validate(project_data(spreadsheet_schemas=schemas))


# --- BuildContext -------------------------------------------------------------


def test_build_context_initialises_stage_results():
    ctx = make_context()
    assert ctx.stage_results == [None, None]
    assert ctx.is_active
    assert ctx.build_id != make_context().build_id


@pytest.mark.parametrize(
    "value,expected,data",
    [
        ((), "completed", {}),
        (((), {"a": 1}), "completed", {"a": 1}),
        (("skipped", {"why": "x"}), "skipped", {"why": "x"}),
        ("paused", "paused", {}),
        ({"a": 1}, "completed", {"a": 1}),
    ],
)
def test_set_stage_result(value, expected, data):
    ctx = make_context()
    ctx.current_stage = 1
    log = Log()
    log.warning(type="w")

    ctx.set_stage_result(Success(value, log))

    assert ctx.stage_results[0] is None
    result = ctx.stage_results[1]
    assert result is not None
    assert (result.result, result.data) == (expected, data)
    assert result.log.warnings == [{"type": "w"}]


def test_set_stage_result_failed():
    ctx = make_context()
    ctx.current_stage = 0
    log = Log()
    log.error(type="e")

    ctx.set_stage_result(Err(log))

    result = ctx.stage_results[0]
    assert result is not None and result.result == "failed"
    assert result.log.errors == [{"type": "e"}]


def test_set_stage_result_requires_running_stage():
    with pytest.raises(ValueError):
        make_context().set_stage_result(Success(()))


def test_artifacts():
    ctx = make_context()

    ctx.add_intermediate_artifact(ctx.project.files["upper"], "Stage")
    ctx.add_final_artifact("out/merged.owl", "Other", final_path="merged.owl")
    ctx.add_source_artifact("upper.xlsx", "Source")

    assert [(a.local_path, a.final_path, a.kind, a.origin) for a in ctx.artifacts] == [
        ("upper.owl", "upper.owl", "intermediate", "Stage"),
        ("out/merged.owl", "merged.owl", "final", "Other"),
        ("upper.xlsx", None, "source", "Source"),
    ]


def test_artifact_paths_are_relative_to_build_dir():
    ctx = make_context()

    artifact = ctx.add_final_artifact(os.path.abspath("build/out/a.owl"), "Stage", final_path="a.owl")

    assert artifact.local_path == os.path.join("out", "a.owl")
    assert ctx.artifact(str(artifact.id)) is artifact


def test_final_artifacts_keep_latest_per_final_path():
    ctx = make_context()
    ctx.add_final_artifact("first.owl", "A", final_path="merged.owl")
    ctx.add_intermediate_artifact("tmp.owl", "A", final_path="tmp.owl")
    latest = ctx.add_final_artifact("second.owl", "B", final_path="merged.owl")
    other = ctx.add_final_artifact("upper.owl", "B", final_path="upper.owl")

    assert ctx.final_artifacts() == [latest, other]


def test_build_context_is_immutable_where_frozen():
    ctx = make_context()
    with pytest.raises(ValidationError):
        ctx.build_dir = "elsewhere"
