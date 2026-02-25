"""
Web/Flask implementation of ReleaseContext.

This context is used when running release steps in the web application,
with Flask, SQLAlchemy database, and GitHub API support.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Literal, List

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query

from ..database.Release import Release, ReleaseArtifact
from ..model.ReleaseScript import ReleaseScript
from ..model.RepositoryConfiguration import RepositoryConfiguration
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..utils import download_file, github
from .ReleaseContext import ReleaseContext
from .common import (
    fetch_assert_release,
    local_name,
    set_release_info,
    update_release,
    next_release_step,
    set_release_result,
    add_artifact,
    get_artifacts,
)


class WebReleaseContext(ReleaseContext):
    """
    Web/Flask implementation of ReleaseContext.
    
    Uses SQLAlchemy for database operations, Flask-GitHub for repository access,
    and stores release progress in the database for the web UI.
    """
    
    _logger = logging.getLogger(__name__)
    
    _config: ConfigurationService
    _working_dir: str
    _release_id: int
    _release_script: ReleaseScript
    _gh: GitHub
    _db: SQLAlchemy
    _q: Query[Release]
    _a: Query[ReleaseArtifact]
    
    def __init__(
        self,
        db: SQLAlchemy,
        gh: GitHub,
        release_script: ReleaseScript,
        release_id: int,
        tmp: str,
        config: ConfigurationService,
    ):
        """
        Initialize a web release context.
        
        :param db: SQLAlchemy database instance.
        :param gh: Flask-GitHub instance.
        :param release_script: The release script configuration.
        :param release_id: The database ID of the release.
        :param tmp: The working directory path.
        :param config: Configuration service.
        """
        self._config = config
        self._db = db
        self._gh = gh
        self._release_script = release_script
        self._release_id = release_id
        self._q = db.session.query(Release)
        self._a = db.session.query(ReleaseArtifact)
        self._working_dir = tmp
        
    @property
    def is_interactive(self) -> bool:
        return True

    @property
    def release_script(self) -> ReleaseScript:
        return self._release_script
    
    @property
    def repo_config(self) -> RepositoryConfiguration:
        """Get the repository configuration for the current release script."""
        config = self._config.get(self._release_script.full_repository_name)
        assert config is not None, (
            f"Repository configuration for '{self._release_script.full_repository_name}' not found."
        )
        return config
    
    @property
    def working_dir(self) -> str:
        return self._working_dir
    
    @property
    def gh(self) -> GitHub:
        """Get the GitHub API client."""
        return self._gh

    @property
    def config_service(self) -> ConfigurationService:
        """Get the configuration service."""
        return self._config

    @property
    def release_id(self) -> int:
        """Get the database release ID."""
        return self._release_id

    def canceled(self) -> bool:
        """Check if the release has been canceled in the database."""
        r: Release = fetch_assert_release(self._q, self._release_id)
        return r.state == "canceled"

    def local_name(self, remote_name: str, file_ending: Optional[str] = None) -> str:
        """
        Get the local path for a downloaded remote file name.
        
        :param remote_name: The remote file name or path.
        :param file_ending: Optional file ending to replace.
        :return: The local file path corresponding to the remote file.
        """
        return local_name(self._working_dir, remote_name, file_ending)

    def save_file(self, file: str, temporary: Optional[bool] = None, **kwargs):
        """
        Save a file (store as artifact).
        
        :param file: The file path to save.
        :param temporary: Whether the file is temporary.
        """
        self.store_artifact(file, kind="intermediate" if temporary else "final")

    def update_progress(
        self,
        *,
        position: Optional[Tuple[int, int]] = None,
        progress: Optional[float] = None,
        current_item: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Update the progress of the release step in the database.
        
        :param position: A tuple indicating the current progress (current step, total steps).
        :param progress: A float indicating the progress percentage (0.0 to 1.0).
        :param current_item: Name or description of the current item being processed.
        :param message: Message to provide additional context about the progress.
        """
        self.set_release_info(dict(__progress=dict(
            position=position,
            progress=progress if progress is not None else (
                (position[0] / position[1]) if position is not None else None
            ),
            current_item=current_item,
            message=message,
        )))

    def set_release_info(self, details: dict) -> None:
        """Update release information in the database."""
        set_release_info(self._q, self._release_id, details)

    def set_release_result(self, result: Result) -> None:
        """Set the release result in the database."""
        set_release_result(self._q, self._release_id, result)

    def next_release_step(self) -> None:
        """Advance to the next release step in the database."""
        next_release_step(self._q, self._release_id)

    def update_release(self, patch: dict) -> None:
        """Update release database fields directly."""
        update_release(self._q, self._release_id, patch)

    def download(self, file: str, local_name: Optional[str] = None) -> str:
        """
        Download a file from the GitHub repository.
        
        :param file: The file path in the repository.
        :param local_name: Optional local file path. If None, uses local_name(file).
        :return: The local file path.
        """
        if local_name is None:
            local_name = self.local_name(file)
        
        download_file(
            self._gh,
            self._release_script.full_repository_name,
            file,
            local_name,
        )
        
        return local_name

    def store_artifact(
        self,
        local_path: str,
        target_path: Optional[str] = None,
        kind: Optional[Literal["source", "intermediate", "final"]] = None,
        downloadable: bool = True,
    ) -> None:
        """Store an artifact in the database."""
        kind = kind if kind is not None else ("intermediate" if target_path is None else "final")
        
        artifact = ReleaseArtifact(
            release_id=self._release_id,
            local_path=local_path,
            target_path=target_path,
            kind=kind,
            downloadable=downloadable,
        )
        
        add_artifact(self._db, artifact)

    def get_artifacts(self) -> List[ReleaseArtifact]:
        """Get all artifacts for this release from the database."""
        return get_artifacts(self._a, self._release_id)

    def calculate_release_name(self) -> str:
        """
        Calculate a release name based on the current date and existing releases.
        
        Checks GitHub for existing releases with the same date and increments
        the version number if needed.
        
        :return: A release name in the format vYYYY-MM-DD[.n].
        """
        release_name = f"v{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        last_release = github.get_latest_release(
            self._gh,
            self._release_script.full_repository_name,
        )
        
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

    def cleanup(self) -> None:
        """Web context does not clean up the working directory (managed by do_release)."""
        pass
