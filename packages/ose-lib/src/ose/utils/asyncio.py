import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine
from weakref import WeakKeyDictionary, ref


async def check_cancelled():
    await asyncio.sleep(0)

def max_concurrency(n: int):
    if n < 1:
        raise ValueError("Concurrency must be positive")

    def decorator(fn):
        # Active calls keep the semaphore alive. Weak references in both directions
        # avoid retaining a closed loop through Semaphore._loop.
        semaphores = WeakKeyDictionary()
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            semaphore_ref = semaphores.get(loop)
            semaphore = semaphore_ref() if semaphore_ref is not None else None
            if semaphore is None:
                semaphore = asyncio.Semaphore(n)
                semaphores[loop] = ref(semaphore)
            async with semaphore:
                return await fn(*args, **kwargs)
        return wrapper
    return decorator

def as_thread[**P, T](func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    Runs `func` in a thread. A thread cannot be interrupted, so if the awaiting task is cancelled, the cancellation
    only takes effect once `func` has returned. Otherwise, the task would end while `func` still works, e.g. on files
    or a git repository.
    """
    @wraps(func)
    async def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        future = asyncio.ensure_future(asyncio.to_thread(func, *args, **kwargs))
        try:
            await asyncio.wait([future])
            return future.result()
        except asyncio.CancelledError:
            while not future.done():
                try:
                    await asyncio.wait([future])
                except asyncio.CancelledError:
                    continue
            # Cancellation takes precedence, but retrieve a worker exception so
            # asyncio does not report it as an unhandled task exception.
            if not future.cancelled():
                future.exception()
            raise
    return inner
