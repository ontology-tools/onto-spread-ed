import asyncio
import inspect
import logging
import traceback
from importlib.metadata import entry_points
from types import ModuleType
from typing import Callable

from ose.result import Err, Log, Success, is_successful
from ose.building.BuildContext import _BuildContextStageResult, BuildContext, BuildState
from ose.building.Progress import Progress
from ose.building import stages as builtin_stage_module
from ose.building.stages import BuildStage
from ose.utils.logging import log_prefix

STAGE_ENTRY_POINT_GROUP = "ose.build_stages"

type ProgressCallback[C: BuildContext] = Callable[[C, Progress], None]
type StageDoneCallback[C: BuildContext] = Callable[
    [C, BuildStage, _BuildContextStageResult], None
]


def _stages_in(module: ModuleType) -> dict[str, type[BuildStage]]:
    return {
        cls.name(): cls
        for _, cls in inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BuildStage) and not inspect.isabstract(cls)
    }


def available_stages() -> dict[str, type[BuildStage]]:
    stages = _stages_in(builtin_stage_module)
    for ep in entry_points(group=STAGE_ENTRY_POINT_GROUP):
        stages |= _stages_in(ep.load())

    return stages


async def run_build[C: BuildContext](
    context: C,
    on_progress: ProgressCallback[C] | None = None,
    on_stage_done: StageDoneCallback[C] | None = None,
) -> C:
    """
    Runs the stages of the build from `context.next_stage()` on, until one fails or pauses, or all completed. Raises
    a `ValueError` without running anything if the build configuration uses unavailable stages.
    """
    logger = logging.getLogger(__name__)
    
    def report_progress(progress: Progress) -> None:
        if on_progress is not None:
            on_progress(context, progress)

    with log_prefix(logger, str(context.build_id)):
        stage_classes = available_stages()
        stage_configs = context.build_configuration.stages

        unknown_stages = [s.name for s in stage_configs if s.name not in stage_classes]
        if unknown_stages:
            raise ValueError(f"Unknown build stages: {', '.join(unknown_stages)}")

        start = context.next_stage()
        if start is None:
            logger.info("Nothing to do, all stages completed")
            context.state = "completed"
            return context

        logger.info(f"Running build from stage {start + 1}/{len(stage_configs)}")
        context.state = "running"
        
        stages = [
            stage_classes[s.name](s, context)
            for s in stage_configs[start:]
        ]

        for i, stage in enumerate(stages, start=start):
            context.current_stage = i

            logger.debug(
                f"Starting build stage {i + 1}/{len(stage_configs)}: {stage.name()}"
            )

            try:
                result = await stage.run(on_progress_update=report_progress)
            except asyncio.CancelledError:
                cancelled = context.set_stage_result(Success("cancelled"))
                context.state = "cancelled"
                if on_stage_done is not None:
                    on_stage_done(context, stage, cancelled)
                raise
            except Exception as e:
                logger.exception(f"Build stage {stage.name()} raised an exception")
                log = Log()
                log.error(
                    type="exception",
                    msg=str(e),
                    traceback="".join(traceback.format_exception(e)),
                )
                result = Err(log)

            stage_result = context.set_stage_result(result)

            state: BuildState = "running"
            if not is_successful(result):
                last_error = result.log.errors[-1] if len(result.log.errors) > 0 else ""
                logger.error(f"Build stage {stage.name()} failed: {last_error}")
                state = "errored"
            elif stage_result.result in ("paused", "cancelled"):
                state = stage_result.result
            elif i == len(stage_configs) - 1:
                state = "completed"
            context.state = state

            if on_stage_done is not None:
                on_stage_done(context, stage, stage_result)

            if state != "running":
                break

        return context
