import asyncio
import os
import threading
import types
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Any, Callable

import pytest
from flask import Flask, g
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ose.building import STAGE_ENTRY_POINT_GROUP, BuildStage
from ose.building import run as run_module
from ose.project import Project
from ose.result import Err, Log, Success
from ose.utils.asyncio import as_thread

from ose_app.database.Base import Base
from ose_app.database.Release import Release
from ose_app.database.User import User
from ose_app.release.runner import ReleaseJob, ReleaseRunner
from ose_app.release.stages import CleanupStage, ReleaseContext
from ose_app.routes.api.release import release_cancel


class Recording(BuildStage):
    calls: list[str] = []

    @classmethod
    def name(cls) -> str:
        return "RECORD"

    async def run(self, on_progress_update=None):
        Recording.calls.append(self.name())
        return Success(())


class Failing(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "FAIL"

    async def run(self, on_progress_update=None):
        log = Log()
        log.error(type="broken")
        return Err(log)


class Pausing(BuildStage):
    @classmethod
    def name(cls) -> str:
        return "PAUSE"

    async def run(self, on_progress_update=None):
        return Success(("paused", {}))


class Hanging(BuildStage):
    starts: list[str] = []

    @classmethod
    def name(cls) -> str:
        return "HANG"

    async def run(self, on_progress_update=None):
        Hanging.starts.append(self.context.project.short_name)
        await asyncio.sleep(30)
        return Success(())


class Blocking(BuildStage):
    """Works in a thread until `release` is set"""

    release = threading.Event()
    finished: list[bool] = []

    @classmethod
    def name(cls) -> str:
        return "BLOCK"

    async def run(self, on_progress_update=None):
        await as_thread(self._work)()
        return Success(())

    def _work(self) -> None:
        Blocking.release.wait(10)
        Blocking.finished.append(True)


class FakeEntryPoint:
    def __init__(self, module):
        self.module = module

    def load(self):
        return self.module


@pytest.fixture(autouse=True)
def stages(monkeypatch):
    Recording.calls = []
    Hanging.starts = []
    Blocking.release = threading.Event()
    Blocking.finished = []
    module = types.ModuleType("runner_test_stages")
    for cls in [BuildStage, Recording, Failing, Pausing, Hanging, Blocking, CleanupStage]:
        setattr(module, cls.__name__, cls)
    monkeypatch.setattr(
        run_module, "entry_points", lambda group: [FakeEntryPoint(module)] if group == STAGE_ENTRY_POINT_GROUP else []
    )


@pytest.fixture
def runner():
    return partial(
        ReleaseRunner, poll_interval=0.02, heartbeat_interval=0.02, lease_timeout=0.2, progress_interval=0
    )


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'ose.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add(User("token", id=1, github_login="user"))
        s.commit()
    return engine


def project(short_name: str, *stages: str) -> Project:
    return Project.model_validate({
        "short_name": short_name,
        "full_name": "Example Ontology",
        "iri_prefix": "http://example.org/",
        "short_repository_name": short_name.lower(),
        "full_repository_name": f"example/{short_name.lower()}",
        "prefixes": {"EX": "http://example.org/EX_"},
        "external": {"sources": ["external.xlsx"], "target": "external.owl"},
        "files": {},
        "build_configurations": [{"name": "default", "stages": [{"name": s} for s in stages]}],
    })


def add_release(engine, tmp_path, *stages: str, repo: str = "EX", **values: Any) -> int:
    p = project(repo, *stages)
    build_dir = tmp_path / f"build-{repo}"
    build_dir.mkdir(exist_ok=True)
    context = ReleaseContext(
        project=p,
        build_configuration=p.build_configuration("default"),
        build_dir=str(build_dir),
        github_token="token",
    )
    with Session(engine) as s:
        release = Release(**{
            "state": "starting",
            "repo": repo,
            "context": context.model_dump(mode="json"),
            "requested_action": "run",
            "requested_by": "user",
            **values,
        })
        s.add(release)
        s.commit()
        return release.id


def get(engine, release_id: int) -> Release:
    with Session(engine) as s:
        release = s.get(Release, release_id)
        assert release is not None
        s.expunge(release)
        return release


def update(engine, release_id: int, **values: Any) -> None:
    with Session(engine) as s:
        release = s.get(Release, release_id)
        for k, v in values.items():
            setattr(release, k, v)
        s.commit()


def result_kinds(release: Release) -> list[str | None]:
    return [r["result"] if r is not None else None for r in release.context["stage_results"]]  # type: ignore[index]


async def wait_for(condition: Callable[[], bool], timeout: float = 5) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not condition():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("Condition not met in time")
        await asyncio.sleep(0.01)


def run_runner(runner: ReleaseRunner, scenario: Callable[[], Any]) -> None:
    """Runs the runner while `scenario` runs, then stops it"""

    async def main():
        task = asyncio.create_task(runner.run())
        try:
            await scenario()
        finally:
            runner.stop()
            await asyncio.wait_for(task, 10)

    asyncio.run(main())


def given_back(release: Release) -> bool:
    return release.worker_id is None and release.heartbeat_at is None


@pytest.mark.parametrize("requested_by, expected_token", [("user", "token"), ("missing", None), (None, None)])
def test_loads_requester_token_by_github_username(engine, tmp_path, runner, requested_by, expected_token):
    with Session(engine) as s:
        s.add(User("starter-token", github_login="starter"))
        s.commit()
    release_id = add_release(engine, tmp_path, "RECORD", started_by="starter", requested_by=requested_by)

    context, token, state = ReleaseJob(runner(engine), release_id, "run")._load()

    assert get(engine, release_id).as_dict()["requested_by"] == requested_by
    assert token == expected_token
    assert context.github_token == (expected_token or "")
    assert state == "starting"


def test_runs_a_requested_release(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "RECORD", "RECORD")

    async def scenario():
        await wait_for(lambda: get(engine, release_id).end is not None)

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert r.state == "completed" and given_back(r) and r.requested_action is None
    assert Recording.calls == ["RECORD", "RECORD"]
    assert result_kinds(r) == ["completed", "completed"]


def test_completes_an_empty_build(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path)

    async def scenario():
        await wait_for(lambda: get(engine, release_id).end is not None)

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert r.state == "completed" and given_back(r) and r.requested_action is None


def test_continues_a_paused_release(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "PAUSE", "RECORD")

    async def scenario():
        await wait_for(lambda: get(engine, release_id).state == "paused" and given_back(get(engine, release_id)))
        assert get(engine, release_id).end is None
        update(engine, release_id, requested_action="run")
        await wait_for(lambda: get(engine, release_id).end is not None)

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert r.state == "completed" and result_kinds(r) == ["paused", "completed"]


def test_skips_a_failed_stage(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "FAIL", "RECORD")

    async def scenario():
        await wait_for(lambda: get(engine, release_id).state == "errored" and given_back(get(engine, release_id)))
        update(engine, release_id, requested_action="skip")
        await wait_for(lambda: get(engine, release_id).end is not None)

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert r.state == "completed" and result_kinds(r) == ["skipped", "completed"]


def test_records_errors_outside_of_stages(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "UNKNOWN")

    async def scenario():
        await wait_for(lambda: get(engine, release_id).state == "errored" and given_back(get(engine, release_id)))

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert result_kinds(r) == ["failed"]
    assert r.context["stage_results"][0]["log"]["errors"][0]["type"] == "exception"  # type: ignore[index]


def test_cancellation_stops_without_running_later_stages(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "HANG", "CLEANUP", "RECORD")

    async def scenario():
        await wait_for(lambda: Hanging.starts == ["EX"] and get(engine, release_id).state == "running")
        # As the cancel endpoint does
        update(engine, release_id, state="cancelled", requested_action=None)
        await wait_for(lambda: get(engine, release_id).end is not None)

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert r.state == "cancelled" and given_back(r) and r.requested_action is None
    assert r.context["state"] == "cancelled"  # type: ignore[index]
    assert os.path.exists(tmp_path / "build-EX")
    assert Recording.calls == []


def test_cancellation_waits_for_threads(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "BLOCK")

    async def scenario():
        await wait_for(lambda: get(engine, release_id).state == "running")
        update(engine, release_id, state="cancelled", requested_action=None)
        await asyncio.sleep(0.2)
        assert get(engine, release_id).end is None  # the thread still works

        Blocking.release.set()
        await wait_for(lambda: get(engine, release_id).end is not None)
        assert Blocking.finished == [True]

    run_runner(runner(engine), scenario)


def test_leaves_a_release_cancelled_without_runner_untouched(engine, tmp_path, runner):
    release_id = add_release(
        engine, tmp_path, "PAUSE", state="cancelled", requested_action=None, end=datetime.now(timezone.utc)
    )

    async def scenario():
        await wait_for(lambda: get(engine, release_id).requested_action is None and given_back(get(engine, release_id)))

    run_runner(runner(engine), scenario)

    assert get(engine, release_id).state == "cancelled"
    assert os.path.exists(tmp_path / "build-EX")


@pytest.mark.parametrize("stage_names, expected_state, expected_results, files_remain", [
    (("RECORD", "CLEANUP"), "completed", ["completed", "completed"], False),
    (("FAIL", "CLEANUP"), "errored", ["failed", None], True),
    (("PAUSE", "CLEANUP"), "paused", ["paused", None], True),
    (("RECORD",), "completed", ["completed"], True),
])
def test_cleanup_only_runs_in_configured_sequence(
    engine, tmp_path, runner, stage_names, expected_state, expected_results, files_remain
):
    release_id = add_release(engine, tmp_path, *stage_names)
    release_runner = runner(engine)
    assert release_runner._try_claim(release_id, "run")
    job = ReleaseJob(release_runner, release_id, "run")
    context, _, _ = job._load()
    asyncio.run(job._build(context))
    job._give_back()

    assert get(engine, release_id).state == expected_state
    assert result_kinds(get(engine, release_id)) == expected_results
    assert os.path.exists(tmp_path / "build-EX") == files_remain


@pytest.mark.parametrize("worker_id", [None, "worker"])
def test_cancel_endpoint_clears_requests_without_scheduling_stages(engine, tmp_path, worker_id):
    release_id = add_release(engine, tmp_path, "CLEANUP", requested_action="rerun", worker_id=worker_id)
    app = Flask(__name__)
    with app.test_request_context(), Session(engine) as s:
        g.user = User("token", id=1, github_login="user")
        response = release_cancel.__wrapped__("EX", types.SimpleNamespace(session=s))

    data = response.get_json()
    assert data["state"] == "cancelled"
    assert data["requested_by"] == "user"
    assert data["requested_action"] is None
    assert (data["end"] is not None) == (worker_id is None)
    assert get(engine, release_id).worker_id == worker_id
    assert os.path.exists(tmp_path / "build-EX")


@pytest.mark.parametrize("recover", [False, True])
def test_cancelled_jobs_preserve_files_and_stage_results(engine, tmp_path, runner, recover):
    release_runner = runner(engine)
    release_id = add_release(
        engine, tmp_path, "CLEANUP", state="cancelled", requested_action=None, worker_id=release_runner.worker_id
    )
    job = ReleaseJob(release_runner, release_id, "recover" if recover else "run")
    context, _, state = job._load()
    context.created_branches.add("release/test")

    if recover:
        job._recover(context, state)
    else:
        job.stop("cancel")
        job._stopped(context)
    job._give_back()

    release = get(engine, release_id)
    assert release.state == "cancelled" and release.end is not None and given_back(release)
    assert release.context["state"] == "cancelled"
    assert release.context["created_branches"] == ["release/test"]
    assert result_kinds(release) == [None]
    assert os.path.exists(tmp_path / "build-EX")


def test_shutdown_does_not_restore_request_after_api_cancellation(engine, tmp_path, runner):
    release_runner = runner(engine)
    release_id = add_release(engine, tmp_path, "CLEANUP", worker_id=release_runner.worker_id, requested_action=None)
    job = ReleaseJob(release_runner, release_id, "run")
    job.stop("shutdown")
    job._stopped(None)  # a queued job normally restores its request on shutdown
    update(engine, release_id, state="cancelled", requested_action=None)

    job._give_back()

    assert get(engine, release_id).requested_action is None
    assert not release_runner._try_claim(release_id, "run")


def test_rerun_restarts_a_running_stage(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "HANG")

    async def scenario():
        await wait_for(lambda: Hanging.starts == ["EX"])
        update(engine, release_id, requested_action="rerun")
        await wait_for(lambda: Hanging.starts == ["EX", "EX"])
        await wait_for(lambda: get(engine, release_id).state == "running")

    run_runner(runner(engine), scenario)


def test_shutdown_interrupts_running_releases(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "HANG")

    async def scenario():
        await wait_for(lambda: Hanging.starts == ["EX"])

    run_runner(runner(engine), scenario)

    r = get(engine, release_id)
    assert r.state == "errored" and given_back(r) and r.end is None
    assert result_kinds(r) == ["failed"]
    assert r.context["stage_results"][0]["log"]["errors"][0]["type"] == "interrupted"  # type: ignore[index]


def test_limits_parallel_releases(engine, tmp_path, runner):
    ids = {"A": add_release(engine, tmp_path, "HANG", repo="A"), "B": add_release(engine, tmp_path, "HANG", repo="B")}
    waiting: list[int] = []

    async def scenario():
        await wait_for(lambda: len(Hanging.starts) == 1)
        waiting.append(ids["B" if Hanging.starts == ["A"] else "A"])
        await wait_for(lambda: get(engine, waiting[0]).progress is not None)
        r = get(engine, waiting[0])
        assert r.state == "starting" and r.progress["message"] == "Waiting for other releases to finish"  # type: ignore[index]
        assert len(Hanging.starts) == 1

    run_runner(runner(engine, max_parallel=1), scenario)

    running = ids[Hanging.starts[0]]
    assert get(engine, running).state == "errored"
    # The other one never started, its request is pending again for the next runner
    r = get(engine, waiting[0])
    assert r.state == "starting" and r.requested_action == "run" and given_back(r)


def test_runs_releases_of_different_repositories_in_parallel(engine, tmp_path, runner):
    add_release(engine, tmp_path, "HANG", repo="A")
    add_release(engine, tmp_path, "HANG", repo="B")

    async def scenario():
        await wait_for(lambda: sorted(Hanging.starts) == ["A", "B"])

    run_runner(runner(engine), scenario)


def test_takes_over_releases_of_dead_runners(engine, tmp_path, runner):
    long_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    running = add_release(
        engine, tmp_path, "RECORD", repo="A", state="running", requested_action=None, worker_id="dead",
        heartbeat_at=long_ago,
    )
    update(engine, running, context={**get(engine, running).context, "current_stage": 0})  # type: ignore[dict-item]
    cancelled = add_release(
        engine, tmp_path, "RECORD", repo="B", state="cancelled", requested_action=None, worker_id="dead"
    )
    starting = add_release(engine, tmp_path, "RECORD", repo="C", requested_action=None, worker_id="dead")

    async def scenario():
        await wait_for(lambda: all(given_back(get(engine, i)) for i in (running, cancelled)))
        await wait_for(lambda: get(engine, starting).state == "completed")

    run_runner(runner(engine), scenario)

    r = get(engine, running)
    assert r.state == "errored" and result_kinds(r) == ["failed"]
    assert r.context["stage_results"][0]["log"]["errors"][0]["type"] == "interrupted"  # type: ignore[index]

    r = get(engine, cancelled)
    assert r.end is not None and os.path.exists(tmp_path / "build-B")


def test_does_not_take_over_releases_of_live_runners(engine, tmp_path, runner):
    release_id = add_release(engine, tmp_path, "RECORD")

    async def scenario():
        await wait_for(lambda: get(engine, release_id).end is not None)

    async def both():
        other = runner(engine)
        task = asyncio.create_task(other.run())
        try:
            await scenario()
        finally:
            other.stop()
            await task

    run_runner(runner(engine), both)

    assert Recording.calls == ["RECORD"]  # claimed by exactly one runner


def test_one_open_release_per_repository(engine, tmp_path):
    add_release(engine, tmp_path, "RECORD", repo="A")
    add_release(engine, tmp_path, "RECORD", repo="B")
    add_release(engine, tmp_path, "RECORD", repo="A", state="completed")

    with pytest.raises(IntegrityError):
        add_release(engine, tmp_path, "RECORD", repo="A", state="paused")

    with Session(engine) as s:
        assert len(s.execute(select(Release.id)).all()) == 3
