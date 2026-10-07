import asyncio
from typing import Any, Callable, Coroutine


async def check_cancelled():
    await asyncio.sleep(0)
    
def max_concurrency(n: int):
    semaphore = asyncio.Semaphore(n)
    def decorator(fn):
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await fn(*args, **kwargs)
        return wrapper
    return decorator

def as_thread[**P, T](func: Callable[P, T]) -> Callable[P, Coroutine[Any, Any, T]]:
    async def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        return await asyncio.to_thread(func, *args, **kwargs)
    return inner