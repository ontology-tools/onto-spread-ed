import asyncio
import importlib
import os
import shutil

import pyhornedowl as ho
import pytest

from helpers import RDFS_LABEL, TERM_HEADER, project_data, write_csv, write_owl, write_xlsx
from ose import plugins
from ose.building import (
    BuildStage,
    ConversionStage,
    ExternalImportsStage,
    MergeStage,
    ValidationStage,
    start_build,
)
from ose.building.Progress import ProgressManager
from ose.building.BuildContext import BuildContext
from ose.project import BuildConfiguration, BuildStep, Project
from ose.result import Err, Log, Success, is_err, is_successful

EX = "http://example.org/EX_"
BFO_ENTITY = "http://purl.obolibrary.org/obo/BFO_0000001"
UPPER = [
    ["EX:0000001", "thing", "entity", "A thing.", "Published"],
    ["EX:0000002", "object", "thing", "An object.", "Published"],
    ["EX:0000003", "part", "object", "A part.", "Published"],
]
LOWER = [["EX:0000100", "wheel", "part", "A wheel.", "Published"]]


@pytest.fixture
def build_dir(tmp_path):
    """A build directory containing the spreadsheets of `project_data()` and an already built external.owl"""
    d = tmp_path / "build"
    d.mkdir()
    write_xlsx(d / "upper.xlsx", [TERM_HEADER, *UPPER])
    write_xlsx(d / "lower.xlsx", [TERM_HEADER, *LOWER])
    write_owl(d / "external.owl", {BFO_ENTITY: "entity"}, iri="http://example.org/external.owl")
    return d


def make_context(build_dir, data=None, stage="TEST", args=None, project_dir=None) -> BuildContext:
    project = Project.model_validate(data or project_data())
    return BuildContext(
        project_dir=str(project_dir or build_dir.parent),
        build_dir=str(build_dir),
        project=project,
        state="running",
        build_configuration=BuildConfiguration(name="test", stages=[BuildStep(name=stage, args=args or {})]),
    )


def run_stage(cls: type[BuildStage], ctx: BuildContext):
    return asyncio.run(cls(ctx.build_configuration.stages[0], ctx).run())


def error_types(result) -> list[str]:
    return [e["type"] for e in result.log.errors]


class FakeBuilder:
    """Stands in for the ROBOT based build service, which needs Java, ROBOT and network access"""

    def __init__(self):
        self.builds: list[tuple] = []
        self.merges: list[tuple] = []

    async def build_ontology(self, ontology, outfile, prefixes, dependency_iris, tmp_dir, iri_prefix):
        self.builds.append((ontology, outfile, dependency_iris))
        return Success(())

    async def merge_imports(self, imports, outfile, iri, main_ontology_name, tmp_dir, renamings, new_parents):
        self.merges.append((imports, outfile, iri, main_ontology_name, renamings, new_parents))
        return Success(())


@pytest.fixture
def fake_builder(monkeypatch):
    builder = FakeBuilder()
    for module in ["ose.building.stages.ConversionStage", "ose.building.stages.ExternalImportsStage"]:
        monkeypatch.setattr(importlib.import_module(module), "RobotOntologyBuildService", lambda: builder)
    return builder


# --- ProgressManager ----------------------------------------------------------


def test_progress_manager_reports_progress():
    updates = []
    progress = ProgressManager(updates.append, total_items=2)
    progress.next_item(item="a.owl", message="Building")
    progress.next_item(item="b.owl")

    assert [(u.current_item, u.total_items, u.item, u.message) for u in updates] == [
        (None, 2, None, "Starting"),
        (0, 2, "a.owl", "Building"),
        (1, 2, "b.owl", None),
    ]
    ProgressManager(None).next_item()  # no callback is fine


# --- start_build --------------------------------------------------------------


class RecordingStage(BuildStage):
    calls: list[BuildStep] = []

    @classmethod
    def name(cls) -> str:
        return "RECORD"

    async def run(self, on_progress_update=None):
        RecordingStage.calls.append(self.step_config)
        return Success(((), {"n": self.step_config.args.get("n")}))


class FailingStage(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "FAIL"

    async def run(self, on_progress_update=None):
        log = Log()
        log.error(type="broken")
        return Err(log)


class RaisingStage(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "RAISE"

    async def run(self, on_progress_update=None):
        raise RuntimeError("boom")


@pytest.fixture
def test_stages(monkeypatch):
    RecordingStage.calls = []
    monkeypatch.setattr(plugins, "for_type", lambda typ: {"test": [RecordingStage, FailingStage, RaisingStage]})


def project_with_stages(*stages: dict) -> Project:
    return Project.model_validate(project_data(build_configurations=[{"name": "default", "stages": list(stages)}]))


def test_start_build_runs_stages_in_order(tmp_path, test_stages):
    project = project_with_stages({"name": "RECORD", "args": {"n": 1}}, {"name": "RECORD", "args": {"n": 2}})

    ctx = asyncio.run(start_build(project, "default", str(tmp_path), str(tmp_path / "build")))

    assert [c.args["n"] for c in RecordingStage.calls] == [1, 2]
    assert ctx.state == "completed"
    assert not ctx.is_active
    assert ctx.build_dir == str(tmp_path / "build")
    assert [(r.result, r.data) for r in ctx.stage_results] == [("completed", {"n": 1}), ("completed", {"n": 2})]  # type: ignore[union-attr]


def test_start_build_stops_at_failing_stage(tmp_path, test_stages):
    project = project_with_stages({"name": "FAIL"}, {"name": "RECORD"})

    ctx = asyncio.run(start_build(project, "default", str(tmp_path), str(tmp_path / "build")))

    assert RecordingStage.calls == []
    assert ctx.state == "errored"
    assert ctx.stage_results[0] is not None and ctx.stage_results[0].result == "failed"
    assert ctx.stage_results[0].log.errors == [{"type": "broken"}]
    assert ctx.stage_results[1] is None


def test_start_build_records_exception_as_failed_stage(tmp_path, test_stages):
    project = project_with_stages({"name": "RAISE"}, {"name": "RECORD"})

    ctx = asyncio.run(start_build(project, "default", str(tmp_path), str(tmp_path / "build")))

    assert RecordingStage.calls == []
    assert ctx.state == "errored"
    [error] = ctx.stage_results[0].log.errors  # type: ignore[union-attr]
    assert error["type"] == "exception" and error["msg"] == "boom" and "RuntimeError" in error["traceback"]


def test_start_build_accepts_configuration_object_and_creates_build_dir(tmp_path, test_stages):
    project = project_with_stages()
    config = BuildConfiguration(name="adhoc", stages=[BuildStep(name="RECORD")])

    ctx = asyncio.run(start_build(project, config, str(tmp_path)))

    assert ctx.build_configuration == config
    assert os.path.isdir(ctx.build_dir)
    assert len(RecordingStage.calls) == 1
    shutil.rmtree(ctx.build_dir)


def test_start_build_rejects_unknown_configuration(tmp_path, test_stages):
    with pytest.raises(ValueError, match="'nope' not found"):
        asyncio.run(start_build(project_with_stages(), "nope", str(tmp_path)))


def test_start_build_rejects_unknown_stages(tmp_path, test_stages):
    project = project_with_stages({"name": "RECORD"}, {"name": "NOPE"})

    with pytest.raises(ValueError, match="Unknown build stages: NOPE"):
        asyncio.run(start_build(project, "default", str(tmp_path)))

    assert RecordingStage.calls == []


BUILTIN_STAGES = [ConversionStage, ExternalImportsStage, MergeStage, ValidationStage]


def test_builtin_stage_names_are_unique():
    assert len({s.name() for s in BUILTIN_STAGES}) == len(BUILTIN_STAGES)


@pytest.mark.parametrize("stage", BUILTIN_STAGES, ids=lambda s: s.__name__)
def test_start_build_finds_builtin_stages(tmp_path, monkeypatch, stage):
    monkeypatch.setattr(plugins, "for_type", lambda typ: {})
    ran = []

    async def run(self, on_progress_update=None):
        ran.append(type(self))
        return Success(())

    monkeypatch.setattr(stage, "run", run)

    ctx = asyncio.run(start_build(project_with_stages({"name": stage.name()}), "default", str(tmp_path)))

    assert ran == [stage]
    assert ctx.state == "completed"
    shutil.rmtree(ctx.build_dir)


# --- ValidationStage ----------------------------------------------------------


def test_validation_stage_valid_project(build_dir):
    result = run_stage(ValidationStage, make_context(build_dir, stage="VALIDATION"))

    assert is_successful(result), result.log.errors
    info = result.value
    assert set(info) == {"upper", "lower", "global"}  # type: ignore[arg-type]
    assert all(v["valid"] for v in info.values())  # type: ignore[union-attr]


def test_validation_stage_reports_errors_per_file(build_dir):
    write_xlsx(build_dir / "lower.xlsx", [TERM_HEADER, ["EX:0000100", "wheel", "nonexistent", "A wheel.", "Published"]])

    result = run_stage(ValidationStage, make_context(build_dir, stage="VALIDATION"))

    assert is_err(result)
    assert any(e["type"] == "unknown-parent" and e["origin"] == "lower.xlsx" for e in result.log.errors)


def test_validation_stage_reports_duplicates_across_files(build_dir):
    write_xlsx(build_dir / "lower.xlsx", [TERM_HEADER, ["EX:0000002", "other object", "part", "Other.", "Published"]])

    result = run_stage(ValidationStage, make_context(build_dir, stage="VALIDATION"))

    assert is_err(result)
    assert "duplicate" in error_types(result)


# --- ConversionStage ----------------------------------------------------------


def test_conversion_stage_builds_files_in_dependency_order(build_dir, fake_builder):
    write_csv(build_dir / "rename.csv", [["ID", "NEW LABEL"], ["EX:0000003", "piece"]])
    write_xlsx(build_dir / "lower.xlsx", [TERM_HEADER, ["EX:0000100", "wheel", "piece", "A wheel.", "Published"]])
    data = project_data()
    data["files"]["upper"]["renameTermFile"] = "rename.csv"
    ctx = make_context(build_dir, data, "EXCEL2OWL")

    result = run_stage(ConversionStage, ctx)

    assert is_successful(result), result.log.errors
    [(upper, upper_out, upper_deps), (lower, lower_out, lower_deps)] = fake_builder.builds
    assert (upper.iri(), upper_out) == ("http://example.org/upper.owl", str(build_dir / "upper.owl"))
    assert (lower.iri(), lower_out) == ("http://example.org/lower.owl", str(build_dir / "lower.owl"))
    assert upper_deps == ["http://example.org/external.owl"]
    assert lower_deps == ["http://example.org/upper.owl", "http://example.org/external.owl"]

    thing = upper.term_by_id("EX:0000001")
    assert thing is not None and thing.sub_class_of[0].id == "BFO:0000001"  # resolved from external.owl
    wheel = lower.term_by_id("EX:0000100")
    assert wheel is not None and wheel.sub_class_of[0].id == "EX:0000003"  # resolved from renamed upper term

    assert [(a.local_path, a.kind) for a in ctx.artifacts] == [
        ("upper.owl", "intermediate"),
        ("lower.owl", "intermediate"),
    ]


def test_conversion_stage_fails_on_invalid_spreadsheet(build_dir, fake_builder):
    write_xlsx(build_dir / "upper.xlsx", [TERM_HEADER, ["EX:0000001", "thing", "[EX:2]", "A thing.", "Published"]])

    result = run_stage(ConversionStage, make_context(build_dir, stage="EXCEL2OWL"))

    assert is_err(result)
    assert "invalid-value" in error_types(result)


@pytest.mark.skipif(shutil.which(os.environ.get("ROBOT", "robot")) is None, reason="ROBOT is not installed")
def test_conversion_stage_with_robot(build_dir):
    ctx = make_context(build_dir, stage="EXCEL2OWL", project_dir=build_dir)

    result = run_stage(ConversionStage, ctx)

    assert is_successful(result), result.log.errors
    upper = ho.open_ontology(str(build_dir / "upper.owl"))
    assert upper.get_annotation(EX + "0000002", RDFS_LABEL) == "object"
    assert EX + "0000001" in upper.get_superclasses(EX + "0000002")
    lower = ho.open_ontology(str(build_dir / "lower.owl"))
    assert EX + "0000003" in lower.get_superclasses(EX + "0000100")


# --- MergeStage ---------------------------------------------------------------


def test_merge_stage_merges_owl_sources(build_dir):
    write_owl(build_dir / "a.owl", {EX + "0000001": "thing"})
    write_owl(build_dir / "b.owl", {EX + "0000002": "object"}, {EX + "0000002": EX + "0000001"})
    data = project_data(files={"merged": {"sources": ["a.owl", "b.owl"], "target": "merged.owl"}})

    result = run_stage(MergeStage, make_context(build_dir, data, "MERGE"))

    assert is_successful(result), result.log.errors
    merged = ho.open_ontology(str(build_dir / "merged.owl"))
    assert merged.get_classes() >= {EX + "0000001", EX + "0000002"}
    assert merged.get_superclasses(EX + "0000002") == {EX + "0000001"}
    assert str(merged.get_iri()) == "http://example.org/merged.owl"


@pytest.mark.parametrize("included,expected", [([], ["upper.owl"]), (["lower"], ["upper.owl", "lower.owl"])])
def test_merge_stage_collapses_published_and_included_files(build_dir, included, expected):
    write_owl(build_dir / "upper.owl", {EX + "0000001": "thing"})
    write_owl(build_dir / "lower.owl", {EX + "0000100": "wheel"})
    data = project_data()
    data["files"]["lower"]["target"] = {"file": "lower.owl", "iri": "http://example.org/lower.owl", "publish": False}
    ctx = make_context(build_dir, data, "MERGE", args={"files": included})

    result = run_stage(MergeStage, ctx)

    assert is_successful(result), result.log.errors
    assert [(a.local_path, a.kind) for a in ctx.artifacts] == [(f, "final") for f in expected]
    upper = ho.open_ontology(str(build_dir / "upper.owl"))
    assert EX + "0000001" in upper.get_classes()
    assert str(upper.get_iri()) == "http://example.org/upper.owl"


# --- ExternalImportsStage -----------------------------------------------------


def test_external_imports_stage(build_dir, fake_builder):
    write_xlsx(
        build_dir / "external.xlsx",
        [
            ["Ontology ID", "IRI", "ROOT_ID", "IDs"],
            ["BFO", "http://purl.obolibrary.org/obo/bfo.owl", "entity [BFO:0000001]", "process [BFO:0000015]"],
        ],
    )
    write_csv(
        build_dir / "rename.csv",
        [["ID", "NEW LABEL", "TYPE"], ["ID", "LABEL", "TYPE"], ["BFO:0000001", "thing", "class"]],
    )
    write_csv(build_dir / "parents.csv", [["ID", "NEW PARENT ID"], ["BFO:0000015", "BFO:0000001"]])
    data = project_data()
    data["external"].update(renameTermFile="rename.csv", addParentsFile="parents.csv")
    ctx = make_context(build_dir, data, "EXTERNAL_IMPORTS")

    result = run_stage(ExternalImportsStage, ctx)

    assert is_successful(result), result.log.errors
    [(imports, outfile, iri, name, renamings, new_parents)] = fake_builder.merges
    assert [(i.id, [t.id for t in i.imported_terms]) for i in imports] == [("BFO", ["BFO:0000015"])]
    assert (outfile, iri, name) == (str(build_dir / "external.owl"), "http://example.org/external.owl", "ex")
    assert renamings == [("BFO:0000001", "thing", "class")]
    assert new_parents == [("BFO:0000015", "BFO:0000001", "class")]
    assert [(a.local_path, a.kind) for a in ctx.artifacts] == [("external.owl", "final")]


def test_external_imports_stage_reports_incomplete_rename_rows(build_dir, fake_builder):
    write_xlsx(build_dir / "external.xlsx", [["Ontology ID", "IRI"], ["BFO", "http://purl.obolibrary.org/obo/bfo.owl"]])
    write_csv(build_dir / "rename.csv", [["ID", "NEW LABEL"], ["BFO:0000001"]])
    data = project_data()
    data["external"]["renameTermFile"] = "rename.csv"

    result = run_stage(ExternalImportsStage, make_context(build_dir, data, "EXTERNAL_IMPORTS"))

    assert is_err(result)
    assert error_types(result) == ["invalid-rename-entry"]
