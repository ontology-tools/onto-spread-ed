import asyncio
import os
import shutil
from pathlib import Path

import pyhornedowl as ho
import pytest

from helpers import write_owl
from ose.building.RobotOntologyBuildService import RobotOntologyBuildService
from ose.ontology import ExcelOntology, OntologyImport
from ose.result import Err, Log, Success, is_successful
from ose.schema import TermIdentifier

EX = "http://example.org/EX_"


def an_import(*terms: str, iri: str = "http://example.org/source.owl") -> OntologyImport:
    return OntologyImport(
        id="SRC",
        iri=iri,
        root_id=TermIdentifier(id="EX:0000001", label="thing"),
        imported_terms=[TermIdentifier(id=t, label=t) for t in terms],
        prefixes=[("EX", EX)],
    )


class FakeCommands:
    """Records the commands instead of running them and creates the files they would write"""

    def __init__(self, fail_downloads: bool = False):
        self.commands: list[tuple[list[str], str | None]] = []
        self.fail_downloads = fail_downloads

    async def __call__(self, command: list[str], cwd=None):
        self.commands.append((command, cwd))
        if command[0] == "curl":
            if self.fail_downloads:
                log = Log()
                log.error(type="command-failed")
                return Err(log)
            Path(command[command.index("-o") + 1]).write_text("downloaded")
        elif "--output" in command:
            Path(command[command.index("--output") + 1]).write_text("built")
        return Success("")

    def of(self, kind: str) -> list[tuple[list[str], str | None]]:
        if kind == "curl":
            return [c for c in self.commands if c[0][0] == "curl"]
        if kind == "slim":
            return [c for c in self.commands if "extract" in c[0]]
        return [c for c in self.commands if "merge" in c[0] and "extract" not in c[0]]


@pytest.fixture
def service(tmp_path, monkeypatch):
    service = RobotOntologyBuildService(str(tmp_path / "cache"))
    commands = FakeCommands()
    monkeypatch.setattr(service, "_execute_command", commands)
    return service, commands


def merge(service: RobotOntologyBuildService, imp: OntologyImport, outfile, name: str):
    return service.merge_imports([imp], str(outfile), "http://example.org/external.owl", name,
                                 [("EX:0000002", "renamed", "class")], [])


def test_merge_imports_caches_downloads_and_extracts(service, tmp_path):
    service, commands = service

    first = asyncio.run(merge(service, an_import("EX:0000002"), tmp_path / "a.owl", "a"))
    second = asyncio.run(merge(service, an_import("EX:0000002"), tmp_path / "b.owl", "b"))

    assert is_successful(first) and is_successful(second)
    assert len(commands.of("curl")) == 1
    assert len(commands.of("slim")) == 1  # the same extraction, even for another ontology
    assert len(commands.of("merge")) == 2
    assert (tmp_path / "a.owl").read_text() == (tmp_path / "b.owl").read_text() == "built"

    asyncio.run(merge(service, an_import("EX:0000002", "EX:0000003"), tmp_path / "c.owl", "c"))
    assert len(commands.of("slim")) == 2  # other terms, other extraction


def test_merge_imports_works_in_temporary_directories(service, tmp_path):
    service, commands = service

    async def both():
        return await asyncio.gather(
            merge(service, an_import("EX:0000002"), tmp_path / "a.owl", "a"),
            merge(service, an_import("EX:0000002"), tmp_path / "b.owl", "b"),
        )

    assert all(is_successful(r) for r in asyncio.run(both()))

    work_dirs = [cwd for _, cwd in commands.of("merge")]
    assert len(set(work_dirs)) == 2
    for command, cwd in commands.of("merge"):
        assert cwd is not None and not os.path.exists(cwd)  # removed afterwards
        # merge() requests a renaming, so every merge has a template.
        template = command[command.index("--template") + 1]
        assert os.path.dirname(template) == cwd

    cached = [f for _, _, files in os.walk(tmp_path / "cache") for f in files]
    assert cached and not [f for f in cached if ".part" in f]


def test_failed_downloads_are_not_cached(tmp_path, monkeypatch):
    service = RobotOntologyBuildService(str(tmp_path / "cache"))
    commands = FakeCommands(fail_downloads=True)
    monkeypatch.setattr(service, "_execute_command", commands)

    assert not is_successful(asyncio.run(merge(service, an_import("EX:0000002"), tmp_path / "a.owl", "a")))
    assert os.listdir(tmp_path / "cache" / "robot-download-cache") == []

    commands.fail_downloads = False
    assert is_successful(asyncio.run(merge(service, an_import("EX:0000002"), tmp_path / "a.owl", "a")))
    assert len(commands.of("curl")) == 2


@pytest.mark.skipif(shutil.which(os.environ.get("ROBOT", "robot")) is None, reason="ROBOT is not installed")
def test_merge_imports_with_robot(tmp_path):
    source = write_owl(
        tmp_path / "source.owl",
        {EX + "0000001": "thing", EX + "0000002": "object", EX + "0000003": "other"},
        {EX + "0000002": EX + "0000001", EX + "0000003": EX + "0000001"},
        iri="http://example.org/source.owl",
    )
    service = RobotOntologyBuildService(str(tmp_path / "cache"))
    outfile = tmp_path / "external.owl"

    result = asyncio.run(merge(service, an_import("EX:0000002", iri=Path(source).as_uri()), outfile, "ex"))

    assert is_successful(result), result.log.errors
    external = ho.open_ontology(str(outfile))
    assert EX + "0000002" in external.get_classes()
    assert EX + "0000003" not in external.get_classes()
    # The renaming adds a label, the original one stays
    assert "renamed" in external.get_annotations(EX + "0000002", "http://www.w3.org/2000/01/rdf-schema#label")


def test_build_ontology_requires_local_files_of_dependencies(service, tmp_path):
    service, commands = service

    result = asyncio.run(service.build_ontology(
        ExcelOntology("http://example.org/lower.owl"), str(tmp_path / "lower.owl"), None,
        ["http://example.org/upper.owl"], {"http://example.org/external.owl": str(tmp_path / "external.owl")},
        "http://example.org/",
    ))

    assert not is_successful(result)
    assert [e["type"] for e in result.log.errors] == ["unknown-dependency"]
    assert commands.commands == []


@pytest.mark.parametrize("operation", ["download", "extract"])
def test_cancelled_cache_write_removes_partial_file(tmp_path, monkeypatch, operation):
    service = RobotOntologyBuildService(str(tmp_path / "cache"))
    commands = FakeCommands()
    monkeypatch.setattr(service, "_execute_command", commands)

    async def run():
        imp = an_import("EX:0000002")
        assert is_successful(await merge(service, imp, tmp_path / "first.owl", "first"))
        if operation == "download":
            for path in (tmp_path / "cache" / "robot-download-cache").glob("*.owl"):
                path.unlink()
        else:
            for path in (tmp_path / "cache" / "robot-slim-cache").glob("*.owl"):
                path.unlink()
        started = asyncio.Event()

        async def cancelled_command(command, cwd=None):
            if command[0] == "curl" or "extract" in command:
                output_flag = "-o" if command[0] == "curl" else "--output"
                Path(command[command.index(output_flag) + 1]).write_text("partial")
                started.set()
                await asyncio.Event().wait()
            return await commands(command, cwd)

        monkeypatch.setattr(service, "_execute_command", cancelled_command)
        task = asyncio.create_task(merge(service, imp, tmp_path / "second.owl", "second"))
        await asyncio.wait_for(started.wait(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not list((tmp_path / "cache").rglob("*.part.owl"))

    asyncio.run(run())


def test_relative_paths_are_absolute_in_robot_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("build").mkdir()
    service = RobotOntologyBuildService("cache")
    commands = FakeCommands()
    monkeypatch.setattr(service, "_execute_command", commands)
    assert is_successful(asyncio.run(merge(service, an_import("EX:0000002"), "build/external.owl", "ex")))
    assert is_successful(asyncio.run(service.build_ontology(
        ExcelOntology("http://example.org/lower.owl"), "build/lower.owl", None,
        ["http://example.org/external.owl"], {"http://example.org/external.owl": "build/external.owl"},
        "http://example.org/",
    )))
    for command, cwd in commands.commands:
        if cwd is None:
            continue
        for index, argument in enumerate(command[:-1]):
            if argument in ("--input", "--output", "--template", "--catalog"):
                assert Path(command[index + 1]).is_absolute()
    assert Path("build/lower.owl").exists()
    assert Path("build/external.owl").exists()


def test_cache_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("OSE_ROBOT_CACHE_DIR", str(tmp_path / "configured"))
    service = RobotOntologyBuildService()
    assert service._download_dir == str(tmp_path / "configured" / "robot-download-cache")


def test_cache_refresh_invalidates_extraction(service, tmp_path, monkeypatch):
    service, commands = service
    imp = an_import("EX:0000002")
    assert is_successful(asyncio.run(merge(service, imp, tmp_path / "a.owl", "ex")))
    downloaded = next((tmp_path / "cache" / "robot-download-cache").glob("*.owl"))
    downloaded.write_text("changed source")
    assert is_successful(asyncio.run(merge(service, imp, tmp_path / "b.owl", "ex")))
    assert len(commands.of("slim")) == 2
    os.utime(downloaded, (0, 0))
    assert is_successful(asyncio.run(merge(service, imp, tmp_path / "c.owl", "ex")))
    assert len(commands.of("curl")) == 2


def test_imports_xml_escapes_iris(tmp_path):
    from xml.etree import ElementTree

    output = tmp_path / "imports.owl"
    RobotOntologyBuildService._write_imports_file(
        str(output), 'http://example.org/?a=1&b="2"', ['http://example.org/?a=1&b="2"']
    )
    root = ElementTree.parse(output)
    imports = root.findall(".//{http://www.w3.org/2002/07/owl#}imports")
    assert imports[0].attrib["{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource"] == 'http://example.org/?a=1&b="2"'
