import contextlib
import logging


class PrefixFilter(logging.Filter):
    def __init__(self, prefix):
        super().__init__()
        self.prefix = prefix

    def filter(self, record):
        record.msg = f"{self.prefix} {record.msg}"
        return True

@contextlib.contextmanager
def log_prefix(logger: logging.Logger, *prefixes: str, **kwargs: str):
    prefix = "".join([f"[{p}]" for p in prefixes] + [f"[{key}={value}]" for key, value in kwargs.items()])
    
    f = PrefixFilter(prefix)
    logger.addFilter(f)
    try:
        yield
    finally:
        logger.removeFilter(f)