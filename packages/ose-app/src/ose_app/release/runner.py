import asyncio
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Coroutine

from flask_sqlalchemy import SQLAlchemy

from ose.building import Progress, run_build

from ose_app.database.Release import OPEN_STATES, Release
from ose_app.release.stages import ReleaseContext

_logger = logging.getLogger(__name__)

CANCEL_POLL_INTERVAL = 2
"""Seconds between checks whether a running release was cancelled"""


def load_context(release: Release, github_token: str) -> ReleaseContext:
    return ReleaseContext.model_validate({**(release.context or {}), "github_token": github_token})


def save_context(db: SQLAlchemy, release_id: int, context: ReleaseContext) -> None:
    release = _fetch(db, release_id)
    # A cancellation requested by a user must not be overwritten by the worker
    state = "cancelled" if release.state == "cancelled" else context.state

    release.context = {**context.model_dump(mode="json"), "state": state}
    release.state = state
    if state not in OPEN_STATES and release.end is None:
        release.end = datetime.now(timezone.utc)
    db.session.commit()


async def run_release(db: SQLAlchemy, release_id: int, github_token: str) -> None:
    release = _fetch(db, release_id)
    if release.state == "cancelled":
        return

    context = load_context(release, github_token)

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
        db.session.commit()


async def _cancel_when_requested(db: SQLAlchemy, release_id: int, build: asyncio.Task) -> None:
    while not build.done():
        await asyncio.sleep(CANCEL_POLL_INTERVAL)
        if not build.done() and _fetch(db, release_id).state == "cancelled":
            build.cancel()



def _fetch(db: SQLAlchemy, release_id: int) -> Release:
    db.session.expire_all()  # see changes of other requests and workers
    release = db.session.get(Release, release_id)
    if release is None:
        raise ValueError(f"Release with id '{release_id}' not found.")
    return release
