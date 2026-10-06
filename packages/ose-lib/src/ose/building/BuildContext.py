from datetime import datetime
from typing import Any, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator
from uuid import UUID, uuid4

from ose.project import BuildConfiguration, Project, ProjectFile
from ose.result import Log, Result, is_successful

if TYPE_CHECKING:
    from ose.building.stages import StageResult

type BuildArtifactFile = str | ProjectFile


def _to_local_path(file: BuildArtifactFile) -> str:
    if isinstance(file, str):
        return file
    elif isinstance(file, ProjectFile):
        return file.target.file
    else:
        raise ValueError(f"Invalid BuildArtifactFile type: {type(file)}")


class BuildArtifact(BaseModel):
    # id = mapped_column(Integer(), primary_key=True)
    # release_id = mapped_column(Integer(), ForeignKey('releases.id'))

    local_path: str
    final_path: Optional[str] = None
    # downloadable: bool = True
    kind: Literal["source", "intermediate", "final"]
    origin: str
    creation_time: datetime


BuildState = Literal[
    "starting", "running", "completed", "cancelled", "errored", "paused"
]


class _BuildContextStageResult(BaseModel):
    log: Log
    data: dict[str, Any]
    result: Literal["skipped", "cancelled", "paused", "failed", "completed"]


class BuildContext(BaseModel):
    project_dir: str = Field(frozen=True)
    """
    The directory where the project is located.
    """
    build_dir: str = Field(frozen=True)
    """
    A directory where build artifacts and temporary files can be stored during the build process.
    """

    project: Project = Field(frozen=True)
    """
    The project being built.
    """

    artifacts: list[BuildArtifact] = []
    """
    A list of artifacts generated during the build.
    """

    build_id: UUID = Field(default_factory=uuid4, frozen=True)
    """
    A unique identifier for this build context.
    """

    build_configuration: BuildConfiguration = Field(frozen=True)
    """
    The build configuration used for this build.
    """

    current_stage: Optional[int] = None
    """
    The current stage of the build as index for build_configuration.stages.
    """

    state: BuildState
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
        self.stage_results = [None for _ in self.build_configuration.stages]
        return self

    def set_stage_result(self, result: Result[StageResult]):
        result_type: Literal["skipped", "cancelled", "paused", "failed", "completed"]
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
                case (t, d):
                    result_type = t
                    data = d
                case str():
                    result_type = result.value

        self.stage_results[self.current_stage] = _BuildContextStageResult(
            log=result.log, data=data, result=result_type
        )

    def _add_artifact(
        self,
        file: BuildArtifactFile,
        kind: Literal["source", "intermediate", "final"],
        origin: str,
        final_path: Optional[str] = None,
    ):
        local_path = _to_local_path(file)
        origin = origin if origin is not None else type(self).__name__
        final_path = (
            final_path
            if final_path is not None
            else (file.target.file if isinstance(file, ProjectFile) else None)
        )
        artifact = BuildArtifact(
            local_path=local_path,
            final_path=final_path,
            kind=kind,
            origin=origin,
            creation_time=datetime.now().astimezone(),
        )
        self.artifacts.append(artifact)

    def _add_source_artifact(
        self,
        file: BuildArtifactFile,
        origin: str,
        final_path: Optional[str] = None,
    ):
        self._add_artifact(file, kind="source", origin=origin, final_path=final_path)

    def _add_intermediate_artifact(
        self,
        file: BuildArtifactFile,
        origin: str,
        final_path: Optional[str] = None,
    ):
        self._add_artifact(
            file, kind="intermediate", origin=origin, final_path=final_path
        )

    def _add_final_artifact(
        self,
        file: BuildArtifactFile,
        origin: str,
        final_path: Optional[str] = None,
    ):
        self._add_artifact(file, kind="final", origin=origin, final_path=final_path)
