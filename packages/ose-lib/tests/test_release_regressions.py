"""Regressions found when reproducing BCIO v2026-09-29 locally."""

import asyncio
import importlib
import os
from pathlib import Path
import shutil
from unittest.mock import AsyncMock

import pyhornedowl as ho
import pyhornedowl.model as hom
import pytest

from helpers import TERM_HEADER, project_data, write_owl, write_xlsx
from ose.building import run_build
from ose.building.BuildContext import BuildContext
from ose.building.RobotOntologyBuildService import RobotOntologyBuildService
from ose.building.stages import ConversionStage
from ose.project import BuildConfiguration, BuildStep, Project
from ose.result import Success, is_successful
from ose.schema import OWLPropertyType
from ose.schema.ColumnMapping import RelationColumnMapping
from ose.schema.Schema import DEFAULT_SCHEMA


@pytest.mark.parametrize(
    "prefix,property_type", [("REL", OWLPropertyType.ObjectProperty), ("ANN", OWLPropertyType.AnnotationProperty)]
)
@pytest.mark.parametrize("suffix", ["", " [BFO:0000051]", " [RO_0000051]"])
def test_builtin_relation_headers_allow_display_id(prefix: str, property_type: OWLPropertyType, suffix: str) -> None:
    mapping = DEFAULT_SCHEMA.get_mapping("terms.xlsx", f"{prefix} 'has part'{suffix}")
    assert isinstance(mapping, RelationColumnMapping)
    assert mapping.relation.label == "has part"
    assert mapping.property_type == property_type
    assert mapping.get_value("wheel")[0][0].label == "has part"


def make_context(tmp_path: Path, stages: list[str]) -> BuildContext:
    write_owl(tmp_path / "external.owl", {"http://example.org/EX_0": "entity"}, iri="http://example.org/external.owl")
    write_xlsx(tmp_path / "upper.xlsx", [TERM_HEADER, ["EX:1", "thing", "entity", "A thing.", "Published"]])
    project = Project.model_validate(
        project_data(
            files={
                # The merge target may appear before its source's producer in the config.
                "merged": {"sources": ["upper.owl"], "target": "merged.owl"},
                "upper": {"sources": ["upper.xlsx"], "target": "upper.owl"},
            }
        )
    )
    return BuildContext(
        project=project,
        build_dir=str(tmp_path),
        build_configuration=BuildConfiguration(name="test", stages=[BuildStep(name=s) for s in stages]),
    )


def test_validation_does_not_read_stale_or_absent_merge_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(importlib.import_module("ose.building.run"), "entry_points", lambda **_: [])
    context = make_context(tmp_path, ["VALIDATION"])
    result = asyncio.run(run_build(context))
    assert result.state == "completed"
    stage = result.stage_results[0]
    assert stage is not None
    assert stage.data["merged"]["skipped"]
    assert stage.data["upper"]["valid"]
    assert not (tmp_path / "upper.owl").exists()


def test_conversion_does_not_overwrite_owl_merge_targets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = make_context(tmp_path, ["EXCEL2OWL"])
    target = tmp_path / "merged.owl"
    target.write_text("previous release")
    builder = AsyncMock()
    builder.build_ontology.return_value = Success(())
    module = importlib.import_module("ose.building.stages.ConversionStage")
    monkeypatch.setattr(module, "RobotOntologyBuildService", lambda: builder)
    result = asyncio.run(ConversionStage(context.build_configuration.stages[0], context).run())
    assert is_successful(result), result.log.errors
    builder.build_ontology.assert_awaited_once()
    assert builder.build_ontology.call_args.args[1] == str(tmp_path / "upper.owl")
    assert target.read_text() == "previous release"
    assert all(a.local_path != "merged.owl" for a in context.artifacts)


@pytest.mark.skipif(shutil.which(os.environ.get("ROBOT", "robot")) is None, reason="ROBOT is not installed")
def test_merge_resolves_transitive_imports_locally(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dependency_iri = "https://example.invalid/external.owl"
    write_owl(tmp_path / "external.owl", {"http://example.org/EX_0": "entity"}, iri=dependency_iri)
    module = ho.PyIndexedOntology()
    module.add_component(hom.OntologyID(module.iri("https://example.invalid/module.owl"), None))
    module.add_component(hom.Import(module.iri(dependency_iri)))
    module.save_to_file(str(tmp_path / "module.owl"))
    monkeypatch.chdir(tmp_path)
    # Relative paths must still resolve from the caller's directory when ROBOT
    # runs inside its isolated temporary directory.
    result = asyncio.run(
        RobotOntologyBuildService(str(tmp_path / "cache")).merge_ontologies(
            ["module.owl"],
            "merged.owl",
            "https://example.invalid/merged.owl",
            "https://example.invalid/v1",
            {},
            local_ontologies={dependency_iri: str(tmp_path / "external.owl")},
        )
    )
    assert is_successful(result), result.log.errors
    merged = ho.open_ontology(str(tmp_path / "merged.owl"))
    assert "http://example.org/EX_0" in merged.get_classes()


@pytest.mark.parametrize("reverse", [False, True])
def test_imported_label_resolution_is_stable_and_reports_ambiguity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reverse: bool
) -> None:
    from typing import Any
    from ose.ontology import ExcelOntology

    path = tmp_path / "external.owl"
    write_owl(
        path,
        {"http://example.org/EX_9": "shared", "http://example.org/EX_1": "shared"},
        iri="http://example.org/external.owl",
    )
    ontology = ho.open_ontology(str(path))

    class OntologyView:
        def get_classes(self) -> list[str]:
            return sorted(ontology.get_classes(), reverse=reverse)

        def __getattr__(self, name: str) -> Any:
            return getattr(ontology, name)

    monkeypatch.setattr(ho, "open_ontology", lambda *_: OntologyView())
    external = ExcelOntology.from_owl(str(path), {"EX": "http://example.org/EX_"}).value_or_raise()
    local = ExcelOntology("http://example.org/local.owl")
    local.import_other_excel_ontology(external).value_or_raise()
    local.add_terms_from_list(
        [["EX:2", "child", "shared"], ["EX:3", "explicit", "shared [EX:9]"]],
        ["ID", "Label", "Parent"],
        origin="terms.xlsx",
    ).value_or_raise()
    result = local.resolve()
    assert is_successful(result), result.log.errors
    child = local.term_by_id("EX:2")
    explicit = local.term_by_id("EX:3")
    assert child is not None and child.sub_class_of[0].id == "EX:1"
    assert explicit is not None and explicit.sub_class_of[0].id == "EX:9"
    assert len(result.log.warnings) == 1
    assert result.log.warnings[0]["type"] == "ambiguous-reference"
    assert result.log.warnings[0]["candidates"] == ["EX:1", "EX:9"]
    assert result.log.warnings[0]["origin"] == "terms.xlsx"


def test_label_shared_with_obsolete_terms_is_not_ambiguous() -> None:
    from ose.ontology import ExcelOntology

    local = ExcelOntology("http://example.org/local.owl")
    local.add_terms_from_list(
        [
            ["EX:1", "shared", None, "Obsolete"],
            ["EX:2", "shared", None, "Published"],
            ["EX:3", "shared", None, "Pre-proposed"],
            ["EX:4", "child", "shared", "Published"],
        ],
        ["ID", "Label", "Parent", "Curation status"],
        origin="terms.xlsx",
    ).value_or_raise()
    result = local.resolve()
    assert is_successful(result), result.log.errors
    child = local.term_by_id("EX:4")
    assert child is not None and child.sub_class_of[0].id == "EX:2"
    assert not [w for w in result.log.warnings if w["type"] == "ambiguous-reference"]
