import graphlib
import os
from pydantic import BaseModel, model_validator
from typing import Any, Literal, Optional

from .Schema import Schema


class BuildStep(BaseModel):
    name: str
    args: dict[str, Any] = {}


class BuildConfiguration(BaseModel):
    name: str
    description: Optional[str] = None
    stages: list[BuildStep] = []


class SubOntologyConfiguration(BaseModel):
    release_file: str
    excel_file: str


class ProjectFileSource(BaseModel):
    file: str
    type: Literal["classes", "relations", "individuals", "owl"]
    spreadsheet_schema: str = "default"

    @model_validator(mode="before")
    @classmethod
    def _from_filename(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"file": data, "type": "owl" if data.endswith(".owl") else "classes"}
        return data


class BuildTarget(BaseModel):
    file: str
    iri: str
    ontology_annotations: dict[str, str] = {}
    publish: bool = True


class ProjectFile(BaseModel):
    sources: list[ProjectFileSource]
    target: BuildTarget
    needs: list[str] = []
    renameTermFile: Optional[str] = None
    addParentsFile: Optional[str] = None


class Project(BaseModel):
    short_name: str
    full_name: str

    id_digits: int = 6
    main_branch: str = "main"
    prefixes: dict[str, str] = {}
    subontologies: dict[str, SubOntologyConfiguration] = {}

    readonly_files: dict[str, str] = {}

    validation: list[Literal["include-external", "include-dependencies"]] = [
        "include-external",
        "include-dependencies",
    ]

    iri_prefix: str
    short_repository_name: str
    full_repository_name: str

    external: ProjectFile
    files: dict[str, ProjectFile]

    build_configurations: list[BuildConfiguration]
    
    spreadsheet_schemas: dict[str, Schema] = {}

    @model_validator(mode="before")
    @classmethod
    def _expand_shorthands(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        def expand_target(project_file: Any) -> Any:
            if isinstance(project_file, dict) and isinstance(
                target := project_file.get("target"), str
            ):
                iri = data.get("iri_prefix", "") + os.path.basename(target)
                return {**project_file, "target": {"file": target, "iri": iri}}
            return project_file

        if "external" in data:
            data["external"] = expand_target(data["external"])
        if isinstance(data.get("files"), dict):
            data["files"] = {k: expand_target(v) for k, v in data["files"].items()}

        return data

    @model_validator(mode="after")
    def _check_needs(self) -> "Project":
        named_files = {"external": self.external, **self.files}
        errors = [
            f"'{name}' needs the unknown file '{n}'"
            for name, f in named_files.items()
            for n in f.needs
            if n not in self.files
        ] + [
            f"'{name}' uses the unknown spreadsheet schema '{s}'"
            for name, f in named_files.items()
            for s in f.sources
            if s.spreadsheet_schema not in self.spreadsheet_schemas
        ]
        if errors:
            raise ValueError("; ".join(errors))

        try:
            graphlib.TopologicalSorter({name: f.needs for name, f in self.files.items()}).prepare()
        except graphlib.CycleError as e:
            raise ValueError(f"Cyclic dependency between files: {' -> '.join(reversed(e.args[1]))}")
        
        return self