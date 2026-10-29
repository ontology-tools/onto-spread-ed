import asyncio
import importlib
from importlib.metadata import entry_points

import openpyxl
import pytest

from ose.building import BuildContext, available_stages, run_build
from ose.project import Project, BuildConfiguration, BuildStep
from ose.result import Err, Log, Success


PLUGIN_STAGES = {"BCIO_SEARCH", "ADDICTO_VOCAB", "HIERARCHICAL_SPREADSHEETS", "ANNOTATION_SHEETS"}


def test_installed_plugin_stages_are_discovered():
    assert PLUGIN_STAGES <= available_stages().keys()
    assert not entry_points(group="ose.plugins")


@pytest.fixture
def context(tmp_path):
    project = Project.model_validate({
        "short_name": "EX", "full_name": "Example", "iri_prefix": "http://example.org/",
        "short_repository_name": "ex", "full_repository_name": "example/ex",
        "external": {"sources": [], "target": "external.owl"},
        "files": {}, "build_configurations": [],
    })
    return BuildContext(project=project, build_dir=str(tmp_path), build_configuration=BuildConfiguration(name="test"))


@pytest.mark.parametrize("name", ["BCIO_SEARCH", "ADDICTO_VOCAB"])
def test_search_stage_runs_async_and_preserves_http_errors(context, monkeypatch, name):
    cls = available_stages()[name]
    module = importlib.import_module(cls.__module__)
    ontology = module.ExcelOntology
    monkeypatch.setattr(ontology, "from_owl", lambda *args: Success(ontology("")))
    service = module.BCIOSearchService if name == "BCIO_SEARCH" else module.AddictOVocabService

    async def update(self, *args):
        log = Log()
        log.error(type="http-error", status_code=503, response={"hydra:title": "Unavailable"})
        return Err(log)

    monkeypatch.setattr(service, "update_api", update)
    configuration = BuildConfiguration(name="test", stages=[BuildStep(name=name, args={"included_files": []})])
    context = BuildContext(project=context.project, build_dir=context.build_dir, build_configuration=configuration)
    asyncio.run(run_build(context))
    assert context.state == "errored"
    result = context.stage_results[0]
    assert result.log.errors[0]["status_code"] == 503
    assert result.data["errors"] == result.log.errors


def test_annotation_stage_reads_intro_in_build_directory_and_registers_artifact(context):
    intro = openpyxl.Workbook()
    intro.active["A1"] = "Instructions"
    intro.create_sheet("Discard")
    intro.save(f"{context.build_dir}/intro.xlsx")
    step = BuildStep(name="ANNOTATION_SHEETS", args={
        "included_files": [], "intro_sheet": "intro.xlsx", "output_filename": "template.xlsx",
    })
    stage = available_stages()[step.name](step, context)
    assert asyncio.run(stage.run()).successful
    artifact = context.final_artifacts()[0]
    assert artifact.final_path == "template.xlsx"
    workbook = openpyxl.load_workbook(f"{context.build_dir}/{artifact.local_path}")
    assert workbook.sheetnames == ["Sheet"]
    assert workbook.active["A1"].value == "Instructions"


def test_concurrent_search_declaration_errors_are_all_reported():
    from types import SimpleNamespace
    from ose_plugin_bcio.BCIOSearchService import BCIOSearchService
    from ose_plugin_hbcp.search_api.HttpError import HttpError

    class Client:
        async def declare_term(self, term):
            await asyncio.sleep(0)
            if term.id == "EX:3":
                raise HttpError(502, "Bad gateway", {"hydra:title": "Bad gateway"})
            log = Log()
            log.error(type="http-error", term=term.id, status_code=503)
            return Err(log)

        async def update_term(self, *args):
            pytest.fail("Failed declarations must not be queued for update")

    service = BCIOSearchService({}, None)
    service._api_client = Client()
    terms = [SimpleNamespace(id=f"EX:{n}", label=f"Term {n}", curation_status=lambda: "Proposed") for n in range(4)]
    ontology = SimpleNamespace(terms=lambda: terms)
    result = asyncio.run(service.update_api(ontology, [], "Test release"))
    assert result.failed
    assert len(result.log.errors) == 4
    assert {e["term"] for e in result.log.errors if "term" in e} == {"EX:0", "EX:1", "EX:2"}
    assert any(e["status_code"] == 502 for e in result.log.errors)


def test_hierarchical_stage_registers_final_workbook(context, monkeypatch):
    from types import SimpleNamespace
    import networkx as nx
    from ose.project import ProjectFile

    context.project.files["module"] = ProjectFile.model_validate({
        "sources": [], "target": {"file": "release/ex_module.owl", "iri": "http://example.org/module.owl"},
    })
    step = BuildStep(name="HIERARCHICAL_SPREADSHEETS", args={"included_files": ["module"]})
    stage = available_stages()[step.name](step, context)
    graph = nx.DiGraph()
    graph.add_node("http://example.org/EX_1", label="Example", definition="A definition")
    ontology = SimpleNamespace(get_id_for_iri=lambda iri: "EX:1")
    monkeypatch.setattr(stage, "build_hierarchy", lambda file: (graph, ontology))
    assert asyncio.run(stage.run()).successful
    artifact = context.final_artifacts()[0]
    assert artifact.final_path == "release/ex-module-hierarchy.xlsx"
    workbook = openpyxl.load_workbook(f"{context.build_dir}/{artifact.local_path}")
    assert workbook.active["A2"].value == "EX:1"
    assert workbook.active["B2"].value == "Example"
