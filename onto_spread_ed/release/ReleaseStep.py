import abc
import os
from typing import Tuple, Optional, Literal, List

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query

from .common import ReleaseCanceledException, local_name, set_release_info, update_release, next_release_step, \
    set_release_result, add_artifact, get_artifacts
from ..database.Release import Release, ReleaseArtifact
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ..model.RepositoryConfiguration import RepositoryConfiguration
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..utils import download_file


class ReleaseStep(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        ...

    _config: ConfigurationService
    _working_dir: str
    _release_id: int
    _release_script: ReleaseScript
    _gh: GitHub
    _db: SQLAlchemy
    _q: Query[Release]

    _total_items: Optional[int] = None
    _current_item: int = 1

    def __init__(self, db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int, tmp: str,
                 config: ConfigurationService) -> None:
        self._config = config
        self._db = db
        self._gh = gh
        self._release_script = release_script
        self._release_id = release_id
        self._q = db.session.query(Release)
        self._a = db.session.query(ReleaseArtifact)
        self._working_dir = tmp

    @property
    def _repo_config(self) -> RepositoryConfiguration:
        return self._config.get(self._release_script.full_repository_name)

    def _update_progress(self,
                         *,
                         position: Optional[Tuple[int, int]] = None,
                         progress: Optional[float] = None,
                         current_item: Optional[str] = None,
                         message: Optional[str] = None):
        self._set_release_info(dict(__progress=dict(
            position=position,
            progress=progress if progress is not None else (
                (position[0] / position[1]) if position is not None else None),
            current_item=current_item,
            message=message
        )))

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

    def _download(self, file: str, local_name: Optional[str] = None):
        if local_name is None:
            local_name = self._local_name(file)

        return download_file(self._gh, self._release_script.full_repository_name, file, local_name)

    def store_artifact(self, local_path: str, target_path: Optional[str] = None,
                       kind: Optional[Literal["source", "intermediate", "final"]] = None,
                       downloadable: bool = True) -> None:
        kind = kind if kind is not None else ("intermediate" if target_path is None else "final")

        artifact = ReleaseArtifact(release_id=self._release_id, local_path=local_path, target_path=target_path,
                                   kind=kind, downloadable=downloadable)

        add_artifact(self._db, artifact)

    def store_target_artifact(self, file: ReleaseScriptFile,
                              kind: Literal["source", "intermediate", "final"] = "final",
                              downloadable: bool = True):
        return self.store_artifact(self._local_name(file.target.file), file.target.file, kind, downloadable)

    def artifacts(self) -> List[ReleaseArtifact]:
        return get_artifacts(self._a, self._release_id)

    def load_externals_ontology(self) -> Result[ExcelOntology]:
        result = Result()
        config = self._config.get(self._release_script.full_repository_name)

        externals_owl = self._local_name(self._release_script.external.target.file)
        if os.path.exists(externals_owl):
            return ExcelOntology.from_owl(externals_owl, config.prefixes)
        else:
            result.error(type="external-owl-missing",
                         msg="The external OWL file is missing. Ensure it is build before this step")
            return result
