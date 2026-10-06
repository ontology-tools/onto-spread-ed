import abc
from os import path
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel

from ..model.Build import BuildContext

from ..model.Project import BuildStep, Project
from ..model.Result import Result


class Progress(BaseModel):
    current_item: int | None
    total_items: int | None
    item: str | None
    message: str | None


class ProgressManager:
    def __init__(
        self,
        on_progress_update: Callable[[Progress], None] | None,
        total_items: int | None = None,
    ):
        self.total_items = total_items
        self.current_item = -1
        self.on_progress_update = on_progress_update

        if self.on_progress_update:
            self.on_progress_update(
                Progress(
                    current_item=None,
                    total_items=self.total_items,
                    item=None,
                    message="Starting",
                )
            )

    def next_item(self, *, item: str | None = None, message: str | None = None):
        self.current_item += 1
        if self.on_progress_update:
            progress = Progress(
                current_item=self.current_item,
                total_items=self.total_items,
                item=item,
                message=message,
            )
            self.on_progress_update(progress)

StageResultType = Literal["skipped", "cancelled", "paused"] | tuple[()]

# class DetailedStageResult(BaseModel):
#     result: StageResultType = ()
#     data: dict = Field(default_factory=dict)
    
StageResult = StageResultType | tuple[StageResultType, dict[str, Any]] | dict[str, Any]

class BuildStage(abc.ABC):
    def __init__(self, step_config: BuildStep, context: BuildContext):
        self.step_config = step_config
        self.context = context
        
    @abc.abstractmethod
    @classmethod
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
