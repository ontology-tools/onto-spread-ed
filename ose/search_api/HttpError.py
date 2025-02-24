import dataclasses
from typing import Any


@dataclasses.dataclass
class HttpError(Exception):
    status_code: int
    message: str
    response: Any
