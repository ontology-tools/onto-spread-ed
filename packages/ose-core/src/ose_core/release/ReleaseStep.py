import abc
import logging
import os
from datetime import datetime
from typing import Tuple, Optional, Literal, List

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query

from .common import ReleaseCanceledException, fetch_assert_release, local_name, set_release_info, update_release, next_release_step, \
    set_release_result, add_artifact, get_artifacts
from ose_app.database.Release import Release, ReleaseArtifact
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ..model.RepositoryConfiguration import RepositoryConfiguration
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..utils import download_file, github


class ReleaseStep(abc.ABC):
    
    _logger = logging.getLogger(__name__)

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
        """
        Return the repository configuration for the current release script.
    
        :rtype: RepositoryConfiguration
        """
        config = self._config.get(self._release_script.full_repository_name)
        assert config is not None, f"Repository configuration for '{self._release_script.full_repository_name}' not found."
        return config   

    def _update_progress(self,
                         *,
                         position: Optional[Tuple[int, int]] = None,
                         progress: Optional[float] = None,
                         current_item: Optional[str] = None,
                         message: Optional[str] = None):
        """
        Update the progress of the release step.
        
        :param position: A tuple indicating the current progress (current step, total steps).
        :type position: Optional[Tuple[int, int]]
        :param progress: A float indicating the progress percentage (0.0 to 1.0). Calculated from position if None.
        :type progress: Optional[float]
        :param current_item: Name or description of the current item being processed.
        :type current_item: Optional[str]
        :param message: Message to provide additional context about the progress.
        :type message: Optional[str]
        """
        self._set_release_info(dict(__progress=dict(
            position=position,
            progress=progress if progress is not None else (
                (position[0] / position[1]) if position is not None else None),
            current_item=current_item,
            message=message
        )))

    def _next_item(self, *, item: Optional[str] = None, message: Optional[str] = None):
        """
        Update the progress to the next item. Requires `self._total_items` to be set.
        
        :param item: Name or description of the current item being processed.
        :type item: Optional[str]
        :param message: Message to provide additional context about the progress.
        :type message: Optional[str]
        """
        position = (self._current_item, self._total_items) if self._total_items is not None else None

        self._update_progress(position=position, current_item=item, message=message)

        self._current_item += 1

    @abc.abstractmethod
    def run(self) -> bool:
        """
        Execute the release step.
        
        The method is executed in the background and may perform long-running blocking operations. However, it should 
        periodically check for cancellation requests via `_raise_if_canceled`.
        
        A release step can store artifacts using `_store_artifact` or `_store_target_artifact`, and retrieve them and artifacts
        from previous steps using `_artifacts`.
        
        The state of the execution should be reported using `_update_progress` and the final result should be set using `_set_release_result`.
        
        Files from the repository can be downloaded using `_download` and are accessible at the local path returned by `_local_name`.
        
        :return: True if the release step completed successfully and the release should continue, False otherwise.
        :rtype: bool
        """
        ...

    def _raise_if_canceled(self):
        """
        Check if the release has been canceled and raise an exception if so. Should be called periodically during long-running operations.
        """
        r: Release = fetch_assert_release(self._q, self._release_id)
        if r.state == "canceled":
            raise ReleaseCanceledException("Release has been canceled!")

    def _local_name(self, remote_name, file_ending=None) -> str:
        """
        Get the local path for a downloaded remote file name.
        
        :param remote_name: The remote file name or path.
        :param file_ending: Optional file ending to replace.
        :return: The local file path corresponding to the remote file.
        :rtype: str
        """
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

    def _store_artifact(self, local_path: str, target_path: Optional[str] = None,
                       kind: Optional[Literal["source", "intermediate", "final"]] = None,
                       downloadable: bool = True) -> None:
        kind = kind if kind is not None else ("intermediate" if target_path is None else "final")

        artifact = ReleaseArtifact(release_id=self._release_id, local_path=local_path, target_path=target_path,
                                   kind=kind, downloadable=downloadable)

        add_artifact(self._db, artifact)

    def _store_target_artifact(self, file: ReleaseScriptFile,
                              kind: Literal["source", "intermediate", "final"] = "final",
                              downloadable: bool = True):
        return self._store_artifact(self._local_name(file.target.file), file.target.file, kind, downloadable)

    def _artifacts(self) -> List[ReleaseArtifact]:
        return get_artifacts(self._a, self._release_id)

    def _load_externals_ontology(self) -> Result[ExcelOntology]:
        result = Result()
        config = self._repo_config

        externals_owl = self._local_name(self._release_script.external.target.file)
        if os.path.exists(externals_owl):
            return ExcelOntology.from_owl(externals_owl, config.prefixes)
        else:
            result.error(type="external-owl-missing",
                         msg="The external OWL file is missing. Ensure it is build before this step")
            return result

    def _calculate_release_name(self) -> str:
        release_name = f"v{datetime.utcnow().strftime('%Y-%m-%d')}"
        last_release = github.get_latest_release(self._gh, self._release_script.full_repository_name)
        if last_release and last_release["name"].startswith(release_name):
            self._logger.info(f"Release {release_name} already exists.")

            # Release follows format vYYYY-MM-DD[.1,2,3...]
            # Release exists, increment the number at the end if it exists
            if "." in last_release["name"]:
                last_number = int(last_release["name"].split(".")[-1])
                release_name += f".{last_number + 1}"
            else:
                release_name += ".1"
        return release_name
