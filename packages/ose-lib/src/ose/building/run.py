import inspect
import logging
from os import path
import sys
import tempfile
from typing import Literal

from ose.model.Result import is_successful

from ..model.Build import BuildContext
from ..model.Project import BuildConfiguration, Project

from .. import plugins

from .BuildStage import BuildStage


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

    current_module = sys.modules[__name__]

    builtin_stages = {
        cls.name(): cls
        for _, cls in inspect.getmembers(current_module, inspect.isclass)
        if cls.__module__ == __name__ and issubclass(cls, BuildStage)
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
        build_configuration=build_configuration
    )
    
    stages = [
        available_stages[s.name](s, build_context, **s.args) for s in build_configuration.stages
    ]

    logger.info(
        f"[{build_context.build_id}] Build context: {build_context.model_dump_json(indent=2)}"
    )
    
    for i, stage in enumerate(stages):
        logger.debug(f"[{build_context.build_id}] Starting build stage {i+1}/{len(stages)}: {stage.name()}")
        build_context.current_stage = i
        result = await stage.run()
        
        build_context.set_stage_result(result=result)
        
        if not is_successful(result):
            logger.error(f"[{build_context.build_id}] Build stage {stage.name()} failed: {result.log.errors[-1] if len(result.log.errors) > 0 else ''}")
            build_context.state = "errored"
            break
                
        build_context.set_stage_result(result=result)
                
                
            
        
        
        
        

    return build_context
