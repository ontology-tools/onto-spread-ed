import abc
from os import path
from pathlib import Path
from typing import Any, Callable, Literal


from ose.building.Progress import Progress

from ose.building.BuildContext import BuildContext

from ose.project import BuildStep, Project
from ose.result import Result

StageResultType = Literal["skipped", "cancelled", "paused"] | tuple[()]

# class DetailedStageResult(BaseModel):
#     result: StageResultType = ()
#     data: dict = Field(default_factory=dict)

StageResult = StageResultType | tuple[StageResultType, dict[str, Any]] | dict[str, Any]


class BuildStage(abc.ABC):
    def __init__(self, step_config: BuildStep, context: BuildContext):
        self.step_config = step_config
        self.context = context

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        raise NotImplementedError()

    @abc.abstractmethod
    async def run(
        self, on_progress_update: Callable[[Progress], None] | None = None
    ) -> Result[StageResult]:
        raise NotImplementedError()

    @property
    def project(self) -> Project:
        return self.context.project

    def _local_name(self, file_path: str, is_dir: bool = False) -> str:
        p = path.join(self.context.build_dir, file_path)

        dir = Path(p) if is_dir else Path(p).parent

        dir.mkdir(parents=True, exist_ok=True)

        return p
