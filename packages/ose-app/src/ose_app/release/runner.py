"""Execute database-backed release requests in a separate process, with leases for ownership and recovery."""

import asyncio
import logging
import os
import socket
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, cast
from uuid import uuid4

from sqlalchemy import CursorResult, Engine, Update, and_, case, func, or_, select, update
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from ose.building import Progress, run_build
from ose.result import Err, Log
from ose.utils.asyncio import as_thread

from ose_app.database.Release import OPEN_STATES, Release, RequestedAction
from ose_app.database.User import User
from ose_app.release.stages import ReleaseContext

_logger = logging.getLogger(__name__)

StopReason = Literal["cancel", "rerun", "shutdown"]

JobAction = RequestedAction | Literal["recover"]


def utcnow() -> datetime:
    """The current time in UTC, without time zone as stored in the database"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def new_worker_id() -> str:
    suffix = f"-{os.getpid()}-{uuid4().hex[:8]}"
    return socket.gethostname()[: 64 - len(suffix)] + suffix


def load_context(release: Release, github_token: str) -> ReleaseContext:
    return ReleaseContext.model_validate({**(release.context or {}), "github_token": github_token})


def updated_rows(session: Session | scoped_session[Any], statement: Update) -> int:
    """Executes an update and returns the number of rows it matched"""
    return cast(CursorResult[Any], session.execute(statement)).rowcount


class ReleaseRunner:
    def __init__(
        self, engine: Engine, max_parallel: int = 2, worker_id: str | None = None, *,
        poll_interval: float = 2.0, heartbeat_interval: float = 10.0,
        lease_timeout: float = 60.0, progress_interval: float = 1.0,
    ) -> None:
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self.lease_timeout = lease_timeout
        self.progress_interval = progress_interval
        self.worker_id = worker_id or new_worker_id()
        self.sessions = sessionmaker(engine)
        self.slots = asyncio.Semaphore(max_parallel)
        self._jobs: dict[int, ReleaseJob] = {}
        self._stopping = asyncio.Event()

    @property
    def jobs(self) -> dict[int, "ReleaseJob"]:
        return dict(self._jobs)

    def stop(self) -> None:
        self._stopping.set()

    async def run(self) -> None:
        _logger.info(f"Release runner {self.worker_id} started")
        heartbeat = asyncio.create_task(self._heartbeat_loop())
        try:
            while not self._stopping.is_set():
                try:
                    self._handle(*self._poll())
                except Exception:
                    _logger.exception("Polling for release requests failed")

                try:
                    await asyncio.wait_for(self._stopping.wait(), self.poll_interval)
                except TimeoutError:
                    pass
        finally:
            jobs = list(self._jobs.values())
            for job in jobs:
                job.stop("shutdown")
            # The heartbeat continues meanwhile, so no other runner takes over the stopping releases
            await asyncio.gather(*(job.task for job in jobs if job.task is not None), return_exceptions=True)
            heartbeat.cancel()
            _logger.info(f"Release runner {self.worker_id} stopped")

    def _poll(self) -> tuple[list[tuple[int, JobAction]], list[tuple[int, str, str | None]]]:
        """Claims requested releases and returns them alongside the state and request of owned releases."""
        with self.sessions() as s:
            requested_releases = s.execute(
                select(Release.id, Release.requested_action)
                .where(Release.requested_action.is_not(None), Release.worker_id.is_(None))
                .order_by(Release.id)
            ).all()
            owned_releases = s.execute(
                select(Release.id, Release.state, Release.requested_action).where(Release.worker_id == self.worker_id)
            ).all()

        claimed: list[tuple[int, JobAction]] = []
        for release_id, action in requested_releases:
            requested = cast(RequestedAction, action)
            if release_id not in self._jobs and self._try_claim(release_id, requested):
                claimed.append((release_id, requested))

        return claimed, [(r[0], r[1], r[2]) for r in owned_releases]

    def _try_claim(self, release_id: int, action: RequestedAction) -> bool:
        """Atomically claim the release only if its request is unchanged."""
        with self.sessions.begin() as s:
            claimed = updated_rows(
                s,
                update(Release)
                .where(
                    Release.id == release_id,
                    Release.worker_id.is_(None),
                    Release.requested_action == action,
                    Release.state.in_(OPEN_STATES),
                )
                .values(worker_id=self.worker_id, heartbeat_at=utcnow(), requested_action=None),
            )
        return claimed == 1

    def _handle(self, claimed: list[tuple[int, JobAction]], owned_releases: list[tuple[int, str, str | None]]) -> None:
        for release_id, state, requested_action in owned_releases:
            job = self._jobs.get(release_id)
            if job is None:
                continue
            if state == "cancelled":
                job.stop("cancel")
            elif requested_action == "rerun":
                job.stop("rerun")

        for release_id, action in claimed:
            self._start_release(release_id, action)

    def _start_release(self, release_id: int, action: JobAction) -> None:
        job = ReleaseJob(self, release_id, action)
        self._jobs[release_id] = job
        job.task = asyncio.create_task(job.run(), name=f"release-{release_id}")
        job.task.add_done_callback(lambda _: self._jobs.pop(release_id, None) if self._jobs.get(release_id) is job else None)

    async def _heartbeat_loop(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self._heartbeat, list(self._jobs))
                if not self._stopping.is_set():
                    for release_id in await asyncio.to_thread(self._take_over_stale):
                        self._start_release(release_id, "recover")
            except Exception:
                _logger.exception("Heartbeat of the release runner failed")
            await asyncio.sleep(self.heartbeat_interval)

    def _heartbeat(self, release_ids: list[int]) -> None:
        """Renew active jobs only, so abandoned claims expire."""
        if not release_ids:
            return
        with self.sessions.begin() as s:
            s.execute(
                update(Release)
                .where(Release.id.in_(release_ids), Release.worker_id == self.worker_id)
                .values(heartbeat_at=utcnow())
            )

    def _take_over_stale(self) -> list[int]:
        cutoff = utcnow() - timedelta(seconds=self.lease_timeout)
        is_stale = or_(Release.heartbeat_at.is_(None), Release.heartbeat_at < cutoff)
        with self.sessions() as s:
            stale = s.execute(select(Release.id, Release.worker_id).where(Release.worker_id.is_not(None), is_stale)).all()

        taken: list[int] = []
        for release_id, worker_id in stale:
            if release_id in self._jobs:
                continue
            with self.sessions.begin() as s:
                claimed = updated_rows(
                    s,
                    update(Release)
                    .where(Release.id == release_id, Release.worker_id == worker_id, is_stale)
                    .values(worker_id=self.worker_id, heartbeat_at=utcnow()),
                )
            if claimed == 1:
                _logger.warning(f"Taking over release {release_id} from release runner {worker_id}, which is gone")
                taken.append(release_id)
        return taken


class ReleaseJob:
    def __init__(self, runner: ReleaseRunner, release_id: int, action: JobAction) -> None:
        self.release_id = release_id
        self.action = action
        self.task: asyncio.Task[None] | None = None
        self._runner = runner
        self._stop_reason: StopReason | None = None
        self._building = False
        self._restore_action: RequestedAction | None = None
        self._last_progress = 0.0

    def stop(self, reason: StopReason) -> None:
        """Cancellation takes precedence over reruns and shutdown."""
        if self._stop_reason is None:
            self._stop_reason = reason
            if self.task is not None:
                self.task.cancel()
        elif reason == "cancel":
            self._stop_reason = reason

    async def run(self) -> None:
        context: ReleaseContext | None = None
        try:
            context, token, state = await as_thread(self._load)()
            match self.action:
                case "recover":
                    self._recover(context, state)
                case _:
                    if not token:
                        raise RuntimeError("No GitHub token of the user who requested the release")
                    if self.action == "skip":
                        context.skip_current_stage()
                    elif self.action == "rerun" and context.current_stage is not None:
                        context.stage_results[context.current_stage] = None
                    await self._build(context)
        except asyncio.CancelledError:
            task = asyncio.current_task()
            if task is not None:
                task.uncancel()  # handled here, the job ends normally
            self._stopped(context)
        except Exception as e:
            _logger.exception(f"Release {self.release_id} failed")
            await as_thread(self._fail)(
                context,
                {"type": "exception", "msg": str(e), "traceback": "".join(traceback.format_exception(e))},
            )
        finally:
            await as_thread(self._give_back)()

    def _load(self) -> tuple[ReleaseContext, str | None, str]:
        with self._runner.sessions() as s:
            release = s.get(Release, self.release_id)
            if release is None:
                raise ValueError(f"Release with id '{self.release_id}' not found.")
            user = (
                s.scalar(select(User).where(User.github_login == release.requested_by))
                if release.requested_by is not None else None
            )
            token = cast(str | None, user.github_access_token) if user is not None else None
            return load_context(release, token or ""), token, release.state

    async def _build(self, context: ReleaseContext) -> None:
        if self._runner.slots.locked():
            self._write(state="starting", progress=self._message(context, "Waiting for other releases to finish"))

        async with self._runner.slots:
            self._write(state="running", progress=None)
            self._building = True
            await run_build(context, self._on_progress, lambda c, _1, _2: self._save(c))
            self._save(context)

    def _recover(self, context: ReleaseContext, state: str) -> None:
        if state == "cancelled":
            context.state = "cancelled"
            self._save(context)
        elif state == "running":
            self._fail(context, {
                "type": "interrupted", "msg": "The release runner running the release stopped responding."
            })
        elif state == "starting":
            self._restore_action = "run"  # it never started, so it can simply start again

    def _stopped(self, context: ReleaseContext | None) -> None:
        reason = self._stop_reason or "shutdown"
        if reason == "cancel":
            if context is not None:
                context.state = "cancelled"
                self._save(context)
            else:
                self._write(state="cancelled")
        elif reason == "rerun":
            pass  # the `rerun` request is still pending, the runner picks it up once the release is given back
        elif not self._building:
            # Nothing ran yet, the next runner picks the request up again
            self._restore_action = "run" if self.action == "recover" else self.action
        else:
            self._fail(context, {
                "type": "interrupted", "msg": "The release runner stopped while the release was running."
            })

    def _fail(self, context: ReleaseContext | None, error: dict[str, Any]) -> None:
        if context is None or not context.build_configuration.stages:
            self._write(state="errored")
            return

        log = Log()
        log.error(**error)
        if context.current_stage is None:
            context.current_stage = 0
        context.set_stage_result(Err(log))
        context.state = "errored"
        self._save(context)

    def _message(self, context: ReleaseContext, message: str) -> dict[str, Any]:
        return {"stage": context.current_stage, "current_item": None, "total_items": None, "item": None,
                "message": message}

    def _on_progress(self, context: ReleaseContext, progress: Progress) -> None:
        now = time.monotonic()
        if now - self._last_progress < self._runner.progress_interval:
            return
        self._last_progress = now
        self._write(progress={"stage": context.current_stage, **progress.model_dump(mode="json")})

    def _save(self, context: ReleaseContext) -> None:
        state = context.state
        if state == "cancelled" and self._stop_reason in ("rerun", "shutdown"):
            # `run_build` reports the stop as cancellation, but only a user cancels a release
            state = "running"
        self._write(context=context.model_dump(mode="json"), state=state)
        self._last_progress = 0.0  # the first progress of the next stage is written right away

    def _write(self, *, state: str | None = None, **values: Any) -> None:
        """Updates the release unless another runner took it over. A cancellation is never overwritten."""
        if state is not None:
            values["state"] = case((Release.state == "cancelled", "cancelled"), else_=state)
        with self._runner.sessions.begin() as s:
            s.execute(
                update(Release)
                .where(Release.id == self.release_id, Release.worker_id == self._runner.worker_id)
                .values(**values)
            )

    def _give_back(self) -> None:
        values: dict[Any, Any] = {
            Release.worker_id: None,
            Release.heartbeat_at: None,
            # The release has fully stopped
            Release.end: case(
                (and_(Release.state.not_in(OPEN_STATES), Release.end.is_(None)), utcnow()), else_=Release.end
            ),
        }
        values[Release.requested_action] = case(
            (Release.state == "cancelled", None),
            else_=func.coalesce(Release.requested_action, self._restore_action),
        )

        with self._runner.sessions.begin() as s:
            s.execute(
                update(Release)
                .where(Release.id == self.release_id, Release.worker_id == self._runner.worker_id)
                .values(values)
            )
