import logging
import os
import tempfile
import threading
import traceback
from datetime import datetime
from typing import List, Dict, Type

from flask_github import GitHub, GitHubError
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query

from ose.release.common import fetch_assert_release
from ose.services.PluginService import PluginService

from .BuildReleaseStep import BuildReleaseStep
from .GithubPublishReleaseStep import GithubPublishReleaseStep
from .HumanVerificationReleaseStep import HumanVerificationReleaseStep
from .ImportExternalReleaseStep import ImportExternalReleaseStep
from .MergeReleaseStep import MergeReleaseStep
from .PreparationReleaseStep import PreparationReleaseStep
from .ReleaseStep import ReleaseStep
from .ValidationReleaseStep import ValidationReleaseStep
from .common import update_release, ReleaseCanceledException, set_release_info
from ..database.Release import Release
from ..model.ReleaseScript import ReleaseScript
from ..services.ConfigurationService import ConfigurationService

BUILT_IN_RELEASE_STEPS: List[Type[ReleaseStep]] = [
    PreparationReleaseStep,
    ValidationReleaseStep,
    ImportExternalReleaseStep,
    BuildReleaseStep,
    MergeReleaseStep,
    HumanVerificationReleaseStep,
    GithubPublishReleaseStep,
]

BUILT_IN_RELEASE_STEPS_DICT: Dict[str, Type[ReleaseStep]] = dict(
    [(r.name(), r) for r in BUILT_IN_RELEASE_STEPS]
)

def do_release(db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int,
               config: ConfigurationService, plugin_service: PluginService) -> None:
    logger = logging.getLogger(__name__)
    
    available_release_steps = BUILT_IN_RELEASE_STEPS_DICT.copy()
    available_release_steps.update(
        (step.name(), step) for step in plugin_service.get_release_steps()
    )

    q: Query[Release] = db.session.query(Release)
    
    try:
        release = fetch_assert_release(q, release_id)

        if release.local_dir:
            tmp = release.local_dir
        else:
            # tmp_dir = os.path.abspath("./release-working-dir/")
            # os.makedirs(tmp_dir, exist_ok=True)
            tmp_dir = tempfile.mkdtemp(f"onto-spread-ed-release-{release_id}")
            tmp = tmp_dir

        last_step = fetch_assert_release(q, release_id).step
        update_release(q, release_id, {
            Release.state: "running",
            Release.worker_id: f"{os.getpid()}-{threading.current_thread().ident}",
            Release.local_dir: tmp
        })

        release_steps = []
        for step in release_script.steps:
            step_ctor = available_release_steps.get(step.name, None)
            if step_ctor is None:
                raise ValueError(f"Unknown release step '{step.name}")

            release_steps.append(step_ctor(db, gh, release_script, release_id, tmp, config, **step.args))

        for i, step in enumerate(release_steps):
            if last_step <= i:
                continu = step.run()
                if not continu:
                    return

                current_step = fetch_assert_release(q, release_id).step
                if current_step <= last_step and i != len(release_steps) - 1:
                    logger.error("The step did not change after a release step was executed. "
                                 "Did an error occur? Not running further release steps.")
                    return

                last_step = current_step

        update_release(q, release_id, {
            Release.state: "completed",
            Release.end: datetime.utcnow(),
            Release.running: False
        })

    except ReleaseCanceledException:
        pass
    except GitHubError as e:
        set_release_info(q, release_id, {"error": {
            "short": "GitHub " + str(e),
            "long": f"While communicating with github ({e.response.url}) the error {str(e)} occurred.",
            "url": e.response.url
        }})
        update_release(q, release_id, {Release.state: "errored"})
    except Exception as e:
        set_release_info(q, release_id, {"error": {"short": str(e), "long": traceback.format_exc()}})
        update_release(q, release_id, {Release.state: "errored"})
        logger.error(traceback.format_exc())
    finally:
        update_release(q, release_id, {Release.worker_id: None})
