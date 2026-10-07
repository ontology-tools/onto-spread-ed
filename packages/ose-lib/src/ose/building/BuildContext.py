import os
import tempfile
from datetime import datetime
from typing import Any, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator
from uuid import UUID, uuid4

from ose.project import BuildConfiguration, Project, ProjectFile
from ose.result import Log, Result, is_successful

if TYPE_CHECKING:
    from ose.building.stages import StageResult

type BuildArtifactFile = str | ProjectFile

ArtifactKind = Literal["source", "intermediate", "final"]


class BuildArtifact(BaseModel):
    id: UUID = Field(default_factory=uuid4, frozen=True)
    local_path: str
    """Path of the file relative to the build directory"""
    final_path: Optional[str] = None
    """Path of the file in the project, if it is published"""
    kind: ArtifactKind
    origin: str
    creation_time: datetime


BuildState = Literal["starting", "running", "completed", "cancelled", "errored", "paused"]

StageResultKind = Literal["skipped", "cancelled", "paused", "failed", "completed"]


class _BuildContextStageResult(BaseModel):
    log: Log
    data: dict[str, Any]
    result: StageResultKind


class BuildContext(BaseModel):
    project: Project = Field(frozen=True)
    """
    The project being built.
    """

    project_dir: str = Field(frozen=True)
    """
    The directory where the project is located.
    """

    build_dir: str = Field(
        frozen=True,
        default_factory=lambda data: tempfile.mkdtemp(prefix=f"ose-build-{data['project'].short_name}-"),
    )
    """
    A directory where build artifacts and temporary files can be stored during the build process. Defaults to a new
    temporary directory.
    """

    build_configuration: BuildConfiguration = Field(frozen=True)
    """
    The build configuration used for this build.
    """

    artifacts: list[BuildArtifact] = []
    """
    A list of artifacts generated during the build.
    """

    build_id: UUID = Field(default_factory=uuid4, frozen=True)
    """
    A unique identifier for this build context.
    """

    current_stage: Optional[int] = None
    """
    The current stage of the build as index for build_configuration.stages.
    """

    state: BuildState = "starting"
    """
    The current state of the build.
    """

    stage_results: list[_BuildContextStageResult | None] = []
    """
    A list of results for each stage of the build.
    """

    @property
    def is_active(self) -> bool:
        return self.state in ["starting", "running", "paused"]

    @model_validator(mode="after")
    def _validate_stage_results(self) -> "BuildContext":
        if len(self.stage_results) != len(self.build_configuration.stages):
            self.stage_results = [None for _ in self.build_configuration.stages]
        return self

    def next_stage(self) -> int | None:
        if self.current_stage is None:
            index = 0
        else:
            result = self.stage_results[self.current_stage]
            should_rerun = result is None or result.result in ("failed", "cancelled")
            index = self.current_stage + should_rerun

        return index if index < len(self.build_configuration.stages) else None

    def skip_current_stage(self) -> _BuildContextStageResult:
        if self.current_stage is None:
            raise ValueError("No active stage")

        result = self.stage_results[self.current_stage]
        r = _BuildContextStageResult(
            log=result.log if result is not None else Log(),
            data=result.data if result is not None else {},
            result="skipped",
        )
        self.stage_results[self.current_stage] = r
        return r

    def set_stage_result(self, result: "Result[StageResult]") -> _BuildContextStageResult:
        result_type: StageResultKind
        data: dict[str, Any] = dict()

        if self.current_stage is None:
            raise ValueError("Not running a stage, cannot set stage result")

        if not is_successful(result):
            result_type = "failed"
        else:
            match result.value:
                case ():
                    result_type = "completed"
                case ((), d):
                    result_type = "completed"
                    data = d
                case dict() as d:
                    result_type = "completed"
                    data = d
                case (t, d):
                    result_type = t
                    data = d
                case str():
                    result_type = result.value

        r = _BuildContextStageResult(log=result.log, data=data, result=result_type)
        self.stage_results[self.current_stage] = r
        return r

    def add_artifact(
        self,
        file: BuildArtifactFile,
        kind: ArtifactKind,
        origin: str,
        final_path: Optional[str] = None,
    ) -> BuildArtifact:
        if isinstance(file, ProjectFile):
            local_path = file.target.file
            final_path = final_path if final_path is not None else file.target.file
        else:
            local_path = os.path.relpath(file, self.build_dir) if os.path.isabs(file) else file

        artifact = BuildArtifact(
            local_path=local_path,
            final_path=final_path,
            kind=kind,
            origin=origin,
            creation_time=datetime.now().astimezone(),
        )
        self.artifacts.append(artifact)
        return artifact

    def add_source_artifact(self, file: BuildArtifactFile, origin: str, final_path: Optional[str] = None):
        return self.add_artifact(file, kind="source", origin=origin, final_path=final_path)

    def add_intermediate_artifact(self, file: BuildArtifactFile, origin: str, final_path: Optional[str] = None):
        return self.add_artifact(
            file, kind="intermediate", origin=origin, final_path=final_path
        )

    def add_final_artifact(self, file: BuildArtifactFile, origin: str, final_path: Optional[str] = None):
        return self.add_artifact(file, kind="final", origin=origin, final_path=final_path)

    def final_artifacts(self) -> list[BuildArtifact]:
        latest = {a.final_path: a for a in self.artifacts if a.kind == "final" and a.final_path is not None}
        return list(latest.values())

    def artifact(self, id: UUID | str) -> BuildArtifact | None:
        return next((a for a in self.artifacts if str(a.id) == str(id)), None)
