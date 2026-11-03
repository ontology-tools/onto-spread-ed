import asyncio
import threading

import pytest

from ose.utils.asyncio import as_thread


def test_as_thread_returns_the_result():
    @as_thread
    def add(a: int, b: int) -> int:
        return a + b

    assert asyncio.run(add(1, 2)) == 3


def test_cancelled_as_thread_waits_for_the_thread():
    started, release = threading.Event(), threading.Event()
    finished = []

    @as_thread
    def work() -> None:
        started.set()
        release.wait(5)
        finished.append(True)

    async def main():
        task = asyncio.create_task(work())
        await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0.05)
        assert not task.done()  # the thread still runs

        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert finished == [True]

    asyncio.run(main())


def test_repeated_cancellation_waits_and_retrieves_worker_exception():
    async def main():
        loop = asyncio.get_running_loop()
        errors = []
        loop.set_exception_handler(lambda _loop, context: errors.append(context))
        started, release = threading.Event(), threading.Event()

        @as_thread
        def work():
            started.set()
            assert release.wait(5)
            raise ValueError("worker failed after cancellation")

        task = asyncio.create_task(work())
        assert await asyncio.to_thread(started.wait, 5)
        try:
            for _ in range(3):
                task.cancel()
                await asyncio.sleep(0.01)
                assert not task.done()
        finally:
            release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0)
        assert errors == []

    asyncio.run(main())


def test_concurrency_limit_across_event_loops():
    from ose.utils.asyncio import max_concurrency

    active = 0
    peak = 0

    @max_concurrency(2)
    async def work():
        nonlocal active, peak
        active += 1
        peak = max(active, peak)
        await asyncio.sleep(0.001)
        active -= 1

    async def run():
        await asyncio.gather(*(work() for _ in range(6)))

    asyncio.run(run())
    asyncio.run(run())
    assert peak == 2
