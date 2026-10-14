import asyncio
import logging
import os
import threading
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

from ose.building import Progress, run_build

from ose_app.database.Release import OPEN_STATES, Release
from ose_app.release.stages import ReleaseContext

_logger = logging.getLogger(__name__)

CANCEL_POLL_INTERVAL = 2
"""Seconds between checks whether a running release was cancelled"""

WAIT_FOR_OTHER_TIMEOUT = 10 * 60
"""Seconds a release waits for other releases of the repository to stop before it proceeds anyway. Guards against a
stale `worker_id` left behind by a crashed process."""


def load_context(release: Release, github_token: str) -> ReleaseContext:
    return ReleaseContext.model_validate({**(release.context or {}), "github_token": github_token})


def save_context(db: SQLAlchemy, release_id: int, context: ReleaseContext) -> None:
    release = _fetch(db, release_id)
    # A cancellation requested by a user must not be overwritten by the worker
    state = "cancelled" if release.state == "cancelled" else context.state

    release.context = {**context.model_dump(mode="json"), "state": state}
    release.state = state
    # `end` is set by the worker once it stopped (or by the cancel endpoint if no worker runs), not here
    db.session.commit()


async def run_release(db: SQLAlchemy, release_id: int, github_token: str) -> None:
    release = _fetch(db, release_id)
    if release.state == "cancelled":
        return

    context = load_context(release, github_token)

    if not await _wait_for_other_releases(db, release_id, context.current_stage):
        return

    release = _fetch(db, release_id)
    release.worker_id = f"{os.getpid()}-{threading.current_thread().ident}"
    release.state = "running"
    release.progress = None
    db.session.commit()

    def on_progress(c: ReleaseContext, progress: Progress) -> None:
        r = _fetch(db, release_id)
        r.progress = {"stage": c.current_stage, **progress.model_dump(mode="json")}
        db.session.commit()

    build = asyncio.create_task(run_build(context, on_progress, lambda c, _1, _2: save_context(db, release_id, c)))
    watcher = asyncio.create_task(_cancel_when_requested(db, release_id, build))

    try:
        await build
    except asyncio.CancelledError:
        current = asyncio.current_task()
        if current is not None and current.cancelling():
            raise

        _logger.info(f"Release {release_id} was cancelled")
    except (Exception, BaseException):
        _logger.exception(f"Release {release_id} failed")
        context.state = "errored"
        save_context(db, release_id, context)
        raise
    finally:
        watcher.cancel()
        r = _fetch(db, release_id)
        r.worker_id = None
        if r.state not in OPEN_STATES and r.end is None:
            r.end = datetime.now(timezone.utc)  # the release has fully stopped
        db.session.commit()


async def _cancel_when_requested(db: SQLAlchemy, release_id: int, build: asyncio.Task) -> None:
    while not build.done():
        await asyncio.sleep(CANCEL_POLL_INTERVAL)
        if not build.done() and _fetch(db, release_id).state == "cancelled":
            build.cancel()


async def _wait_for_other_releases(db: SQLAlchemy, release_id: int, stage: int | None) -> bool:
    """
    Waits until no other release of the same repository has a worker anymore (this includes cancelled releases that
    are still tearing down). Returns False if the release was cancelled while waiting.
    """
    waited = 0.0
    last_blocking: int | None = None
    while True:
        release = _fetch(db, release_id)
        if release.state == "cancelled":
            return False

        blocking = (
            db.session.query(Release.id)
            .filter(Release.repo == release.repo, Release.id != release_id, Release.worker_id.is_not(None))
            .order_by(Release.id)
            .first()
        )
        if blocking is None:
            return True

        if waited >= WAIT_FOR_OTHER_TIMEOUT:
            _logger.warning(f"Release {release_id} stops waiting for release {blocking[0]} and proceeds")
            return True

        if blocking[0] != last_blocking:
            last_blocking = blocking[0]
            release.progress = {
                "stage": stage,
                "current_item": None,
                "total_items": None,
                "item": None,
                "message": f"Waiting for release #{blocking[0]} to stop",
            }
            db.session.commit()

        await asyncio.sleep(CANCEL_POLL_INTERVAL)
        waited += CANCEL_POLL_INTERVAL


def _fetch(db: SQLAlchemy, release_id: int) -> Release:
    db.session.expire_all()  # see changes of other requests and workers
    release = db.session.get(Release, release_id)
    if release is None:
        raise ValueError(f"Release with id '{release_id}' not found.")
    return release
