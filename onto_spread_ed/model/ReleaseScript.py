import os.path
from dataclasses import dataclass, field
from typing_extensions import Self
from typing import List, Dict, Literal, Any, Optional


@dataclass
class ReleaseScriptStep:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReleaseScriptSource:
    file: str
    type: Literal["classes", "relations", "individuals", "owl"]


@dataclass
class ReleaseScriptTarget:
    file: str
    iri: str
    ontology_annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class ReleaseScriptFile:
    sources: List[ReleaseScriptSource]
    target: ReleaseScriptTarget
    needs: List[str] = field(default_factory=list)
    renameTermFile: Optional[str] = None
    addParentsFile: Optional[str] = None

    @classmethod
    def from_json(cls, data: Dict, prefix: str) -> Self:
        fields = {
            "sources": data.get("sources"),
            "target": data.get("target"),
            "needs": data.get("needs", []),
            "renameTermFile": data.get("renameTermFile", None),
            "addParentsFile": data.get("addParentsFile", None),
        }

        for i, f in enumerate(fields["sources"]):
            if isinstance(f, str):
                fields["sources"][i] = ReleaseScriptSource(file=f, type="owl" if f.endswith(".owl") else "classes")
            else:
                fields["sources"][i] = ReleaseScriptSource(**f)

        if isinstance(fields["target"], str):
            fields["target"] = ReleaseScriptTarget(file=fields["target"],
                                                   iri=prefix + os.path.basename(fields["target"]))
        else:
            fields["target"] = ReleaseScriptTarget(**fields["target"])

        return ReleaseScriptFile(**fields)


@dataclass
class ReleaseScript:
    iri_prefix: str
    short_repository_name: str
    full_repository_name: str
    external: ReleaseScriptFile
    files: Dict[str, ReleaseScriptFile]
    steps: List[ReleaseScriptStep]
    prefixes: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict):
        fields = {
            "iri_prefix": data.get("iri_prefix"),
            "short_repository_name": data.get("short_repository_name"),
            "full_repository_name": data.get("full_repository_name"),
            "external": data.get("external"),
            "files": data.get("files"),
            "prefixes": data.get("prefixes", dict()),
            "steps": data.get("steps")
        }

        fields["external"] = ReleaseScriptFile.from_json(fields["external"], fields["iri_prefix"])

        for k, v in fields["files"].items():
            fields["files"][k] = ReleaseScriptFile.from_json(v, fields["iri_prefix"])

        for i, step in enumerate(fields["steps"]):
            if isinstance(step, dict):
                fields["steps"][i] = ReleaseScriptStep(**step)
            else:
                fields["steps"][i] = ReleaseScriptStep(name=step)

        return ReleaseScript(**fields)
