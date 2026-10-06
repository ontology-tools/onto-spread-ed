import inspect
import logging
from os import path
import tempfile
import traceback

from ose.result import Err, Log, is_successful
from ose.building.BuildContext import BuildContext
from ose.project import BuildConfiguration, Project
from ose import plugins
from ose.building import stages as builtin_stage_module
from ose.building.stages import BuildStage


async def start_build(
    project: Project,
    build_configuration: str | BuildConfiguration,
    project_dir: str,
    build_dir: str | None = None,
) -> BuildContext:
    logger = logging.getLogger(__name__)

    logger.debug(
        f"Starting build for project {project.short_name} in directory {project_dir}"
    )

    builtin_stages = {
        cls.name(): cls
        for _, cls in inspect.getmembers(builtin_stage_module, inspect.isclass)
        if issubclass(cls, BuildStage) and not inspect.isabstract(cls)
    }

    plugin_stages = {cls.name(): cls for classes in plugins.for_type(BuildStage).values() for cls in classes}  # type: ignore[type-abstract]

    available_stages = builtin_stages | plugin_stages
    logger.debug(f"Available build stages: {list(available_stages.keys())}")

    if isinstance(build_configuration, str):
        build_config = next(
            (
                bc
                for bc in project.build_configurations
                if bc.name == build_configuration
            ),
            None,
        )
        if build_config is None:
            raise ValueError(f"Build configuration '{build_configuration}' not found")

        build_configuration = build_config

    unknown_stages = [
        s for s in build_configuration.stages if s.name not in available_stages
    ]
    if unknown_stages:
        raise ValueError(
            f"Unknown build stages: {', '.join(s.name for s in unknown_stages)}"
        )

    build_dir = build_dir or tempfile.mkdtemp(prefix=f"ose-build-{project.short_name}")
    project_dir = project_dir or path.curdir

    build_context = BuildContext(
        project_dir=project_dir,
        project=project,
        build_dir=build_dir,
        state="starting",
        build_configuration=build_configuration,
    )

    stages = [
        available_stages[s.name](s, build_context)
        for s in build_configuration.stages
    ]

    logger.info(
        f"[{build_context.build_id}] Build context: {build_context.model_dump_json(indent=2)}"
    )

    build_context.state = "running"
    for i, stage in enumerate(stages):
        logger.debug(
            f"[{build_context.build_id}] Starting build stage {i+1}/{len(stages)}: {stage.name()}"
        )
        build_context.current_stage = i
        try:
            result = await stage.run()
        except Exception as e:
            logger.exception(f"[{build_context.build_id}] Build stage {stage.name()} raised an exception")
            log = Log()
            log.error(type="exception", msg=str(e), traceback="".join(traceback.format_exception(e)))
            result = Err(log)

        build_context.set_stage_result(result=result)

        if not is_successful(result):
            logger.error(
                f"[{build_context.build_id}] Build stage {stage.name()} failed: {result.log.errors[-1] if len(result.log.errors) > 0 else ''}"
            )
            build_context.state = "errored"
            break
    else:
        build_context.state = "completed"

    return build_context
