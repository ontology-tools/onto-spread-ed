import abc
from dataclasses import dataclass
from typing import Callable, Tuple, Optional, Dict, Any

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query

from .common import ReleaseCanceledException, local_name, set_release_info, update_release, next_release_step, \
    set_release_result
from ..database.Release import Release
from ..model.ReleaseScript import ReleaseScript


@dataclass(frozen=True, eq=True, order=True)
class ProgressUpdate:
    position: Optional[Tuple[int, int]]
    progress: Optional[float]
    current_item: Optional[str]
    message: Optional[str]


class ReleaseStep(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        ...

    _config: Dict[str, Any]
    _working_dir: str
    _release_id: int
    _release_script: ReleaseScript
    _gh: GitHub
    _db: SQLAlchemy
    _q: Query[Release]

    _total_items: Optional[int] = None
    _current_item: int = 1

    def __init__(self, db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int, tmp: str, config: Dict[str, Any]) -> None:
        self._config = config
        self._db = db
        self._gh = gh
        self._release_script = release_script
        self._release_id = release_id
        self._q = db.session.query(Release)
        self._working_dir = tmp

    def _update_progress(self,
                         *,
                         position: Optional[Tuple[int, int]] = None,
                         progress: Optional[float] = None,
                         current_item: Optional[str] = None,
                         message: Optional[str] = None):
        self._set_release_info(dict(__progress=dict(
            position=position,
            progress=progress if progress is not None else ((position[0] / position[1]) if position is not None else None),
            current_item=current_item,
            message=message
        )))
        # if self._progress_callback is not None:
        #     self._progress_callback(ProgressUpdate(
        #         position=position,
        #         progress=progress if progress is not None else ((position[0] / position[1]) if position is not None else None),
        #         current_item=current_item,
        #         message=message
        #     ))

    def _next_item(self, *, item: Optional[str] = None, message: Optional[str] = None):
        position = (self._current_item, self._total_items) if self._total_items is not None else None

        self._update_progress(position=position, current_item=item, message=message)

        self._current_item += 1

    @abc.abstractmethod
    def run(self) -> bool:
        ...

    def _raise_if_canceled(self):
        r: Release = self._q.get(self._release_id)
        if r.state == "canceled":
            raise ReleaseCanceledException("Release has been canceled!")

    def _local_name(self, remote_name, file_ending=None) -> str:
        return local_name(self._working_dir, remote_name, file_ending)

    def _set_release_info(self, details) -> None:
        set_release_info(self._q, self._release_id, details)

    def _update_release(self, patch: dict) -> None:
        update_release(self._q, self._release_id, patch)

    def _next_release_step(self) -> None:
        next_release_step(self._q, self._release_id)

    def _set_release_result(self, result):
        set_release_result(self._q, self._release_id, result)
