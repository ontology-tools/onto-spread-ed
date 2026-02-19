"""
CLI implementation of ReleaseContext.

This context is used when running release steps from the command line,
without Flask, database, or GitHub API dependencies.
"""

import logging
import os
import shutil
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Optional, Tuple, Literal, List, Callable

from ..model.ReleaseScript import ReleaseScript
from ..model.RepositoryConfiguration import RepositoryConfiguration
from ..model.Result import Result
from .ReleaseContext import ReleaseContext


@dataclass
class CLIReleaseArtifact:
    """Simple artifact storage for CLI context."""
    local_path: str
    target_path: Optional[str] = None
    kind: str = "intermediate"
    downloadable: bool = True


class CLIReleaseContext(ReleaseContext):
    """
    CLI implementation of ReleaseContext.
    
    Designed for running release steps locally without database or GitHub dependencies.
    Files are read directly from the repository directory.
    """
    
    _logger = logging.getLogger(__name__)
    
    _release_script: ReleaseScript
    _repo_config: RepositoryConfiguration
    _working_dir: str
    _repository_dir: str
    _tempdir: Optional[TemporaryDirectory] = None
    _artifacts: List[CLIReleaseArtifact]
    _current_step: int = 0
    _result: Optional[Result] = None
    _on_progress: Optional[Callable[[dict], None]] = None
    
    def __init__(
        self,
        release_script: ReleaseScript,
        repo_config: RepositoryConfiguration,
        repository_dir: str,
        working_dir: Optional[str] = None,
        on_progress: Optional[Callable[[dict], None]] = None,
    ):
        """
        Initialize a CLI release context.
        
        :param release_script: The release script configuration.
        :param repo_config: The repository configuration.
        :param repository_dir: The path to the local repository.
        :param working_dir: Optional working directory. If None, a temp directory is created.
        :param on_progress: Optional callback for progress updates.
        """
        self._release_script = release_script
        self._repo_config = repo_config
        self._repository_dir = os.path.abspath(repository_dir)
        self._on_progress = on_progress
        self._artifacts = []
        
        if working_dir is None:
            self._tempdir = TemporaryDirectory(prefix="ose-cli-release-")
            self._working_dir = self._tempdir.name
        else:
            self._working_dir = os.path.abspath(working_dir)
            os.makedirs(self._working_dir, exist_ok=True)

    @property
    def release_script(self) -> ReleaseScript:
        return self._release_script
    
    @property
    def repo_config(self) -> RepositoryConfiguration:
        return self._repo_config
    
    @property
    def working_dir(self) -> str:
        return self._working_dir

    @property
    def repository_dir(self) -> str:
        """Get the repository directory where source files are located."""
        return self._repository_dir

    @property
    def current_step(self) -> int:
        """Get the current release step index."""
        return self._current_step
    
    @property
    def result(self) -> Optional[Result]:
        """Get the result of the last completed step."""
        return self._result

    def canceled(self) -> bool:
        """CLI releases are not cancelable by default."""
        return False

    def local_name(self, remote_name: str, file_ending: Optional[str] = None) -> str:
        """
        Get the local path for a file in the working directory.
        
        :param remote_name: The remote/repository file path.
        :param file_ending: Optional file ending to use instead.
        :return: The local file path.
        """
        file_name = os.path.join(self._working_dir, remote_name)
        
        if file_ending is not None:
            file_name = file_name[:file_name.rfind(".")] + file_ending
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        
        return file_name

    def save_file(self, file: str, temporary: Optional[bool] = None, **kwargs):
        """
        Save a file to the working directory.
        
        :param file: The file path to save.
        :param temporary: Whether the file is temporary (ignored for CLI).
        """
        target_path = self.local_name(file)
        
        if os.path.abspath(target_path) != os.path.abspath(file):
            self._logger.debug(f"Saving file '{file}' to '{target_path}'")
            shutil.copy2(file, target_path)

    def update_progress(
        self,
        *,
        position: Optional[Tuple[int, int]] = None,
        progress: Optional[float] = None,
        current_item: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """Update progress, logging to console."""
        progress_info = {
            "position": position,
            "progress": progress if progress is not None else (
                (position[0] / position[1]) if position is not None else None
            ),
            "current_item": current_item,
            "message": message,
        }
        
        # Log progress
        if message:
            if current_item:
                self._logger.info(f"{message}: {current_item}")
            else:
                self._logger.info(message)
        elif current_item:
            self._logger.info(f"Processing: {current_item}")
        
        # Call progress callback if provided
        if self._on_progress:
            self._on_progress(progress_info)

    def set_release_info(self, details: dict) -> None:
        """Store release info (logged for CLI)."""
        self._logger.debug(f"Release info: {details}")
        
        # Extract progress info if present and call callback
        if "__progress" in details and self._on_progress:
            self._on_progress(details["__progress"])

    def set_release_result(self, result: Result) -> None:
        """Store the release result."""
        self._result = result
        
        if result.errors:
            self._logger.warning(f"Step completed with {len(result.errors)} errors")
        if result.warnings:
            self._logger.info(f"Step completed with {len(result.warnings)} warnings")

    def next_release_step(self) -> None:
        """Advance to the next release step."""
        self._current_step += 1
        self._logger.debug(f"Advanced to step {self._current_step}")

    def download(self, file: str, local_name: Optional[str] = None) -> str:
        """
        Download (copy) a file from the repository to the working directory.

        :param file: The file path in the repository.
        :param local_name: Optional local file path. If None, uses local_name(file).
        :return: The local file path.
        """
        if local_name is None:
            local_name = self.local_name(file)

        source_path = os.path.join(self._repository_dir, file)

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Repository file not found: {source_path}")

        # Skip copy if source and target are the same file (working_dir == repository_dir)
        if os.path.abspath(source_path) == os.path.abspath(local_name):
            self._logger.debug(f"Skipping download of '{file}' (already in place)")
            return local_name

        # Ensure target directory exists
        os.makedirs(os.path.dirname(local_name), exist_ok=True)

        # Copy the file
        shutil.copy2(source_path, local_name)
        self._logger.debug(f"Downloaded '{file}' to '{local_name}'")

        return local_name

    def store_artifact(
        self,
        local_path: str,
        target_path: Optional[str] = None,
        kind: Optional[Literal["source", "intermediate", "final"]] = None,
        downloadable: bool = True,
    ) -> None:
        """Store an artifact in the artifact list."""
        kind = kind if kind is not None else ("intermediate" if target_path is None else "final")
        
        artifact = CLIReleaseArtifact(
            local_path=local_path,
            target_path=target_path,
            kind=kind,
            downloadable=downloadable,
        )
        
        self._artifacts.append(artifact)
        self._logger.debug(f"Stored artifact: {local_path} ({kind})")

    def get_artifacts(self) -> List[CLIReleaseArtifact]:
        """Get all stored artifacts."""
        return self._artifacts.copy()

    def cleanup(self) -> None:
        """Clean up temporary resources."""
        super().cleanup()

        if self._tempdir is not None:
            self._tempdir.cleanup()
            self._tempdir = None

    def calculate_release_name(self) -> str:
        """Calculate a release name based on the current date (no GitHub check)."""
        from datetime import datetime
        return f"v{datetime.utcnow().strftime('%Y-%m-%d')}"
