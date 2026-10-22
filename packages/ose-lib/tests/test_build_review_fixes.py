import asyncio
import importlib

import pytest

from helpers import TERM_HEADER, project_data, write_owl, write_xlsx
from ose.building.BuildContext import BuildContext
from ose.building.stages.ConversionStage import ConversionStage
from ose.building.stages.MergeStage import MergeStage
from ose.project import BuildConfiguration, BuildStep, Project
from ose.result import Success, is_err, is_successful

EX = "http://example.org/EX_"
def context(build_dir, data, stage, args=None):
    project = Project.model_validate(data)
    configuration = BuildConfiguration(name="test", stages=[BuildStep(name=stage, args=args or {})])
    return BuildContext(
        build_dir=str(build_dir),
        project=project,
        state="running",
        build_configuration=configuration,
    )


class FakeBuildService:
    def __init__(self):
        self.builds = []

    async def build_ontology(self, ontology, outfile, prefixes, dependency_iris, local_ontologies, iri_prefix):
        self.builds.append(ontology)
        return Success(())


def test_conversion_stage_uses_each_source_spreadsheet_schema(tmp_path, monkeypatch):
    write_owl(tmp_path / "external.owl", {}, iri="http://example.org/external.owl")
    write_xlsx(tmp_path / "upper.xlsx", [["ID", "Term name"], ["EX:0000001", "thing"]])
    write_xlsx(tmp_path / "lower.xlsx", [TERM_HEADER])
    data = project_data(
        spreadsheet_schemas={
            "custom": {"extends": "default", "mappings": [{"type": "label", "columns": ["Term name"]}]}
        }
    )
    data["files"]["upper"]["sources"] = [
        {"file": "upper.xlsx", "type": "classes", "spreadsheet_schema": "custom"}
    ]
    builder = FakeBuildService()
    conversion_module = importlib.import_module("ose.building.stages.ConversionStage")
    monkeypatch.setattr(conversion_module, "RobotOntologyBuildService", lambda: builder)

    result = asyncio.run(ConversionStage(
        BuildStep(name="EXCEL2OWL"), context(tmp_path, data, "EXCEL2OWL")
    ).run())

    assert is_successful(result), result.log.errors
    assert builder.builds[0].find_term_id("thing") == "EX:0000001"


def test_conversion_stage_reports_unknown_source_schema(tmp_path, monkeypatch):
    write_owl(tmp_path / "external.owl", {}, iri="http://example.org/external.owl")
    write_xlsx(tmp_path / "upper.xlsx", [TERM_HEADER, ["EX:0000001", "thing", None, None, "Published"]])
    data = project_data()
    data["files"]["upper"]["sources"] = [
        {"file": "upper.xlsx", "type": "classes"}
    ]
    conversion_module = importlib.import_module("ose.building.stages.ConversionStage")
    monkeypatch.setattr(conversion_module, "RobotOntologyBuildService", FakeBuildService)
    build_context = context(tmp_path, data, "EXCEL2OWL")
    build_context.project.files["upper"].sources[0].spreadsheet_schema = "missing"

    result = asyncio.run(ConversionStage(
        BuildStep(name="EXCEL2OWL"), build_context
    ).run())

    assert is_err(result)
    assert [error["type"] for error in result.log.errors] == ["schema-not-found"]


@pytest.mark.parametrize("sources, inputs", [(["source.owl"], ["source.owl"]), (["source.xlsx"], ["upper.owl"])])
def test_merge_stage_delegates_to_robot(tmp_path, monkeypatch, sources, inputs):
    calls = []

    class RobotService:
        async def merge_ontologies(self, ontologies, outfile, iri, version_iri, annotations):
            calls.append((ontologies, outfile, iri, annotations))
            return Success(())

    merge_module = importlib.import_module("ose.building.stages.MergeStage")
    monkeypatch.setattr(merge_module, "RobotOntologyBuildService", RobotService)
    data = project_data()
    data["files"]["upper"]["sources"] = sources
    data["files"]["upper"]["target"] = {
        "file": "upper.owl",
        "iri": "http://example.org/upper.owl",
        "ontology_annotations": {"http://example.org/source": "curated"},
    }
    data["files"]["lower"]["target"] = {
        "file": "lower.owl", "iri": "http://example.org/lower.owl", "publish": False,
    }
    build_context = context(tmp_path, data, "MERGE")

    result = asyncio.run(MergeStage(BuildStep(name="MERGE"), build_context).run())

    assert is_successful(result), result.log.errors
    assert calls == [(
        [str(tmp_path / file) for file in inputs],
        str(tmp_path / "upper.owl"),
        "http://example.org/upper.owl",
        {"http://example.org/source": "curated"},
    )]
    assert [(artifact.local_path, artifact.kind) for artifact in build_context.artifacts] == [("upper.owl", "final")]
