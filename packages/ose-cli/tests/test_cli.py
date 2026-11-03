from collections.abc import Callable
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types
from typing import Any, cast

from click import Command
from click.testing import CliRunner, Result as CliResult
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
import pyhornedowl as ho
import pytest
import yaml

from ose.building.BuildContext import BuildContext
from ose.building.Progress import Progress
from ose.building.stages import BuildStage, StageResult
from ose.result import Err, Log, Result, Success
from ose_cli.main import cli

type ProjectFixture = tuple[Path, dict[str, Any]]

build_module = importlib.import_module("ose_cli.build")


class ArtifactStage(BuildStage[BuildContext]):
    @classmethod
    def name(cls) -> str:
        return "ARTIFACT"

    async def run(self, on_progress_update: Callable[[Progress], None] | None = None) -> Result[StageResult]:
        root = Path(self.context.build_dir)
        assert (root / "input.txt").read_text() == "original"
        (root / "input.txt").write_text("changed")
        target = root / "nested" / "result.owl"
        target.parent.mkdir(exist_ok=True)
        target.write_text("result")
        self.context.add_final_artifact("nested/result.owl", self.name(), "published/final.owl")
        return Success(())


class FailStage(BuildStage[BuildContext]):
    @classmethod
    def name(cls) -> str:
        return "FAIL"

    async def run(self, on_progress_update: Callable[[Progress], None] | None = None) -> Result[StageResult]:
        log = Log()
        log.error("test-failure", msg="Failed deliberately")
        return Err(log)


class PauseStage(BuildStage[BuildContext]):
    @classmethod
    def name(cls) -> str:
        return "PAUSE"

    async def run(self, on_progress_update: Callable[[Progress], None] | None = None) -> Result[StageResult]:
        return Success(("paused", {"review": True}))


class ReleaseContext(BuildContext):
    token: str


class ReleaseStage(BuildStage[ReleaseContext]):
    @classmethod
    def name(cls) -> str:
        return "RELEASE_ONLY"

    async def run(self, on_progress_update: Callable[[Progress], None] | None = None) -> Result[StageResult]:
        raise AssertionError("Must be skipped")


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectFixture:
    root = tmp_path / "project"
    (root / ".onto-ed").mkdir(parents=True)
    data = dict(
        short_name="EX",
        full_name="Example",
        iri_prefix="http://example.org/",
        short_repository_name="ex",
        full_repository_name="example/ex",
        external=dict(sources=[], target="external.owl"),
        files={"terms": dict(sources=["terms.xlsx"], target="terms.owl")},
        build_configurations=[dict(name="default", stages=[dict(name="ARTIFACT")])],
    )
    (root / ".onto-ed" / "config.yaml").write_text(yaml.safe_dump(data))
    (root / "input.txt").write_text("original")
    wb = openpyxl.Workbook()
    cast(Worksheet, wb.active).append(["ID", "Label", "Parent", "Definition", "Curation status"])
    cast(Worksheet, wb.active).append(["EX:000001", "thing", "", "A thing", "Published"])
    wb.save(root / "terms.xlsx")
    ho.PyIndexedOntology().save_to_file(str(root / "external.owl"))
    monkeypatch.chdir(root)
    module = types.ModuleType("cli_test_stages")
    for cls in [ArtifactStage, FailStage, PauseStage, ReleaseStage]:
        setattr(module, cls.__name__, cls)
    run_module = importlib.import_module("ose.building.run")
    monkeypatch.setattr(run_module, "entry_points", lambda **_: [types.SimpleNamespace(load=lambda: module)])
    return root, data


def invoke(*args: str | Path) -> CliResult:
    return CliRunner().invoke(cli, list(map(str, args)))


def configure(project: ProjectFixture, *stages: str) -> None:
    root, data = project
    data["build_configurations"][0]["stages"] = [dict(name=s) for s in stages]
    (root / ".onto-ed" / "config.yaml").write_text(yaml.safe_dump(data))


def payload(result: CliResult) -> Any:
    assert result.exit_code == 0, (result.output, result.exception)
    return json.loads(result.stdout)


def test_startup_without_flask() -> None:
    code = """
import sys
class BlockFlask:
    def find_spec(self, fullname: str, *args: object) -> None:
        if fullname.split('.')[0] in ('flask', 'injector', 'ose_app'):
            raise AssertionError(fullname)
sys.meta_path.insert(0, BlockFlask())
from ose_cli.main import cli
from click.testing import CliRunner, Result as CliResult
assert CliRunner().invoke(cli, ['--help']).exit_code == 0
"""
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_project_inspection_and_check(project: ProjectFixture) -> None:
    data = payload(invoke("--json", "project", "show"))
    assert list(data["files"]) == ["external", "terms"]
    assert payload(invoke("--json", "project", "check"))["valid"]
    (project[0] / "terms.xlsx").unlink()
    result = invoke("--json", "project", "check")
    assert result.exit_code == 1
    assert "terms.xlsx" in json.loads(result.stdout)["errors"][0]


def test_project_path_and_root_override(project: ProjectFixture, tmp_path: Path) -> None:
    config = tmp_path / "custom.yaml"
    config.write_text(yaml.safe_dump(project[1]))
    assert payload(invoke("-p", config, "--root", project[0], "--json", "project", "check"))["valid"]
    assert payload(invoke("-p", project[0], "--json", "project", "show"))["short_name"] == "EX"


def test_schemas(project: ProjectFixture) -> None:
    root, data = project
    data["spreadsheet_schemas"] = {"custom": {"extends": "default", "ignored": ["Notes"]}}
    (root / ".onto-ed/config.yaml").write_text(yaml.safe_dump(data))
    assert payload(invoke("--json", "project", "schema"))["custom"]["extends"] == "default"
    schema = payload(invoke("project", "schema", "custom"))
    assert schema["mappings"] and "Notes" in schema["ignored"]
    assert invoke("project", "schema", "unknown").exit_code == 1


def test_stages_marks_context_requirement(project: ProjectFixture) -> None:
    stages = {s["name"]: s for s in payload(invoke("--json", "stages"))}
    assert stages["ARTIFACT"]["runnable"]
    assert not stages["RELEASE_ONLY"]["runnable"]
    assert stages["RELEASE_ONLY"]["context"].endswith("ReleaseContext")


def test_build_copies_and_publishes_final_paths(project: ProjectFixture, tmp_path: Path) -> None:
    directory = project[0] / "build"
    out = tmp_path / "output"
    data = payload(invoke("--json", "build", "default", "--build-dir", directory, "--out", out))
    assert data["state"] == "completed"
    assert (project[0] / "input.txt").read_text() == "original"
    assert (directory / "input.txt").read_text() == "changed"
    assert (out / "published/final.owl").read_text() == "result"
    assert not (project[0] / "published/final.owl").exists()
    saved = json.loads((directory / ".ose-build.json").read_text())
    assert BuildContext.model_validate(saved).state == "completed"
    status = payload(invoke("--json", "build", "status", directory))
    assert status["stages"][0]["errors"] == 0


def test_build_write_and_in_place(project: ProjectFixture, tmp_path: Path) -> None:
    directory = tmp_path / "build"
    assert invoke("build", "--build-dir", directory, "--write").exit_code == 0
    assert (project[0] / "published/final.owl").exists()
    assert invoke("build", "--in-place").exit_code == 0
    assert (project[0] / "input.txt").read_text() == "changed"


@pytest.mark.parametrize("keep", [False, True])
def test_temp_cleanup(project: ProjectFixture, keep: bool) -> None:
    result = invoke("--json", "build", *(["--keep"] if keep else []))
    directory = Path(payload(result)["build_dir"])
    assert directory.exists() is keep
    if keep:
        import shutil

        shutil.rmtree(directory)


def test_failure_is_saved_and_resume_can_skip(project: ProjectFixture, tmp_path: Path) -> None:
    directory = tmp_path / "build"
    configure(project, "FAIL", "ARTIFACT")
    result = invoke("--json", "build", "--build-dir", directory)
    assert result.exit_code == 1
    assert json.loads(result.stdout)["state"] == "errored"
    assert invoke("build", "resume", directory).exit_code == 1
    out = tmp_path / "output"
    data = payload(invoke("--json", "build", "resume", directory, "--skip-current", "--out", out))
    assert data["state"] == "completed"
    assert data["stages"][0]["result"] == "skipped"
    assert (out / "published/final.owl").exists()


def test_pause_resume_and_release_skip(project: ProjectFixture, tmp_path: Path) -> None:
    directory = tmp_path / "build"
    configure(project, "RELEASE_ONLY", "PAUSE", "ARTIFACT")
    result = invoke("--json", "build", "--build-dir", directory)
    assert result.exit_code == 1
    assert "Skipping RELEASE_ONLY" in result.stderr
    assert json.loads(result.stdout)["state"] == "paused"
    data = payload(invoke("--json", "build", "resume", directory))
    assert data["state"] == "completed"
    assert data["skipped"][0]["name"] == "RELEASE_ONLY"


@pytest.mark.parametrize(
    "args",
    [
        ("default", "--stage", "ARTIFACT"),
        ("--in-place", "--build-dir", "somewhere"),
        ("--stage", "NOPE"),
        ("missing-config",),
        ("--skip", "NOPE"),
    ],
)
def test_invalid_build_arguments_leave_project_untouched(project: ProjectFixture, args: tuple[str, ...]) -> None:
    assert invoke("build", *args).exit_code != 0
    assert not (project[0] / ".ose-build.json").exists()


def test_skip_and_stage_order(project: ProjectFixture, tmp_path: Path) -> None:
    data = payload(
        invoke(
            "--json",
            "build",
            "--stage",
            "FAIL",
            "--stage",
            "ARTIFACT",
            "--skip",
            "FAIL",
            "--build-dir",
            tmp_path / "build",
        )
    )
    assert [s["name"] for s in data["stages"]] == ["ARTIFACT"]


def test_robot_cache_applies_only_during_run(
    project: ProjectFixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OSE_ROBOT_CACHE_DIR", "previous")
    original = build_module.run_build

    async def recording(*args: Any, **kwargs: Any) -> BuildContext:
        import os

        assert os.environ["OSE_ROBOT_CACHE_DIR"] == str(tmp_path / "cache")
        return await original(*args, **kwargs)

    monkeypatch.setattr(build_module, "run_build", recording)
    assert invoke("build", "--robot-cache", tmp_path / "cache").exit_code == 0
    import os

    assert os.environ["OSE_ROBOT_CACHE_DIR"] == "previous"


def test_validation_report_and_filters(project: ProjectFixture) -> None:
    result = invoke("--json", "validate", "terms")
    assert result.exit_code == 1, result.output
    report = json.loads(result.stdout)["report"]
    assert set(report) == {"terms"}
    assert not report["terms"]["valid"]
    assert any(e["type"] == "no-parent" for e in report["terms"]["errors"])
    directory = Path(json.loads(result.stdout)["build_dir"])
    assert (
        json.loads((directory / ".ose-build.json").read_text())["stage_results"][0]["data"]["terms"] == report["terms"]
    )
    import shutil

    shutil.rmtree(directory)
    data = payload(invoke("--json", "validate", "--exclude", "no-parent"))
    assert data["report"]["terms"]["valid"]
    assert payload(invoke("--json", "validate", "--only", "duplicate"))["report"]["terms"]["valid"]
    assert invoke("validate", "missing").exit_code == 2
    assert invoke("validate", "--only", "not-a-kind").exit_code == 2


def test_externals_default_write_and_out(
    project: ProjectFixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("ose.building.stages.ExternalImportsStage")

    class Builder:
        async def merge_imports(self, imports: list[Any], outfile: str, *args: Any) -> Result[tuple[()]]:
            Path(outfile).write_text("external result")
            return Success(())

    monkeypatch.setattr(module, "RobotOntologyBuildService", Builder)
    assert invoke("externals").exit_code == 0
    assert (project[0] / "external.owl").read_text() == "external result"
    (project[0] / "external.owl").write_text("original")
    assert invoke("externals", "--out", tmp_path / "out").exit_code == 0
    assert (project[0] / "external.owl").read_text() == "original"
    assert (tmp_path / "out/external.owl").read_text() == "external result"


def test_rejects_existing_build_dir_and_escaping_artifacts(
    project: ProjectFixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, data = project
    assert invoke("build", "--build-dir", root).exit_code == 2
    out = tmp_path / "out"
    original = ArtifactStage.run

    async def escaping(self: ArtifactStage, **kwargs: Any) -> Result[StageResult]:
        result = await original(self, **kwargs)
        self.context.artifacts[0].final_path = "../escape.owl"
        return result

    monkeypatch.setattr(ArtifactStage, "run", escaping)
    result = invoke("build", "--build-dir", tmp_path / "build", "--out", out)
    assert result.exit_code == 1
    assert "escapes directory" in result.output
    assert not (tmp_path / "escape.owl").exists()


def test_can_skip_uninstalled_stage(project: ProjectFixture) -> None:
    configure(project, "UNINSTALLED", "ARTIFACT")
    data = payload(invoke("--json", "build", "--skip", "UNINSTALLED"))
    assert data["state"] == "completed"
    assert data["skipped"] == [{"name": "UNINSTALLED", "reason": "--skip"}]


def test_host_registration_requires_no_flask() -> None:
    from ose_cli import init_app

    registrations: list[tuple[Command, str]] = []
    host = types.SimpleNamespace(
        cli=types.SimpleNamespace(add_command=lambda command, name: registrations.append((command, name)))
    )
    init_app(host, object())
    assert registrations == [(cli, "ose")]


def test_resume_uses_saved_project_without_current_config(
    project: ProjectFixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configure(project, "PAUSE", "ARTIFACT")
    directory = tmp_path / "build"
    assert invoke("build", "--build-dir", directory).exit_code == 1
    (project[0] / ".onto-ed/config.yaml").unlink()
    monkeypatch.chdir(tmp_path)
    assert invoke("build", "resume", directory, "--write").exit_code == 0
    assert (project[0] / "published/final.owl").exists()


def test_checks_rename_and_parent_files(project: ProjectFixture) -> None:
    root, data = project
    data["files"]["terms"].update(renameTermFile="rename.csv", addParentsFile="parents.csv")
    (root / ".onto-ed/config.yaml").write_text(yaml.safe_dump(data))
    result = invoke("--json", "project", "check")
    assert result.exit_code == 1
    assert len(json.loads(result.stdout)["errors"]) == 2


def test_validation_respects_project_schema(project: ProjectFixture) -> None:
    root, data = project
    data["spreadsheet_schemas"] = {"custom": {"extends": "default", "ignored": ["Parent"]}}
    data["files"]["terms"]["sources"] = [{"file": "terms.xlsx", "type": "classes", "spreadsheet_schema": "custom"}]
    (root / ".onto-ed/config.yaml").write_text(yaml.safe_dump(data))
    wb = openpyxl.load_workbook(root / "terms.xlsx")
    cast(Worksheet, wb.active)["C2"] = "missing [EX:999999]"
    wb.save(root / "terms.xlsx")
    result = invoke("--json", "validate", "--exclude", "no-parent")
    assert payload(result)["report"]["terms"]["valid"]


@pytest.fixture
def diagnostic_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run(self: FailStage, on_progress_update: Callable[[Progress], None] | None = None) -> Result[StageResult]:
        log = Log()
        log.error(
            "unknown-parent",
            term={"id": "EX:1", "label": "Thing", "origin": ("terms.xlsx", 7)},
            parent={"id": "EX:99", "label": "Missing parent"},
        )
        log.warning("unknown-column", sheet="terms.xlsx", column="Notes")
        log.info("loaded", msg="Loaded 12 terms.")
        log.debug("parser", msg="Finished parsing.")
        return Err(log)

    monkeypatch.setattr(FailStage, "run", run)


def test_colored_result_diagnostics(project: ProjectFixture, tmp_path: Path, diagnostic_stage: None) -> None:
    directory = tmp_path / "build"
    result = CliRunner().invoke(cli, ["build", "--stage", "FAIL", "--build-dir", str(directory)], color=True)
    assert result.exit_code == 1, result.output
    assert "\x1b[31m" in result.stderr
    assert "\x1b[33m" in result.stderr
    assert "\x1b[36m" in result.stderr
    assert "terms.xlsx:7: Thing [EX:1]: Parent could not be resolved." in result.stderr
    assert "Parent: Missing parent [EX:99]" in result.stderr
    assert "(column Notes): Unrecognized spreadsheet column." in result.stderr
    assert "Loaded 12 terms." in result.stderr
    assert "Finished parsing." not in result.stderr
    assert "{'" not in result.output and '{"' not in result.output
    assert "Build stage FAIL failed:" not in result.output
    status = invoke("build", "status", directory)
    assert "ERROR: [unknown-parent]" in status.stderr
    assert "Loaded 12 terms." in status.stderr
    assert "\x1b[" not in status.output


@pytest.mark.parametrize("verbosity", ["-v", "-q", "--json"])
def test_diagnostic_verbosity_and_json(
    project: ProjectFixture, tmp_path: Path, diagnostic_stage: None, verbosity: str
) -> None:
    result = invoke(verbosity, "build", "--stage", "FAIL", "--build-dir", tmp_path / "build")
    assert result.exit_code == 1
    if verbosity == "--json":
        data = json.loads(result.stdout)
        assert data["stages"][0]["log"]["warnings"][0]["type"] == "unknown-column"
        assert "Parent could not be resolved" not in result.stderr
    else:
        assert "ERROR: [unknown-parent]" in result.stderr
        assert ("WARNING:" in result.stderr) is (verbosity == "-v")
        assert ("Loaded 12 terms." in result.stderr) is (verbosity == "-v")
        assert ("DEBUG: [parser]: Finished parsing." in result.stderr) is (verbosity == "-v")
        assert "\x1b[" not in result.output


@pytest.mark.parametrize("verbose", [False, True])
def test_stage_exception_is_formatted_once(
    project: ProjectFixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, verbose: bool
) -> None:
    async def run(self: FailStage, on_progress_update: Callable[[Progress], None] | None = None) -> Result[StageResult]:
        raise RuntimeError("The input could not be read")

    monkeypatch.setattr(FailStage, "run", run)
    result = invoke(*(["-v"] if verbose else []), "build", "--stage", "FAIL", "--build-dir", tmp_path / "build")
    assert result.exit_code == 1
    assert "ERROR: [exception]: The input could not be read" in result.stderr
    assert ("Traceback (most recent call last):" in result.stderr) is verbose
    assert "Build stage FAIL failed:" not in result.stderr
    assert "raised an exception" not in result.stderr
    assert "{'" not in result.stderr
