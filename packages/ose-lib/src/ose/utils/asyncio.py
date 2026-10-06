import asyncio


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