"""
Abstract base class for release context implementations.

The ReleaseContext provides an abstraction layer between release steps and
their execution environment (CLI vs Web/Flask). This allows release steps
to be reused across different contexts while maintaining the same logic.
"""

import abc
from typing import Optional, Tuple, Literal, List, TYPE_CHECKING

from ..commands.CommandContext import CommandContext

if TYPE_CHECKING:
    from flask_github import GitHub
    from ..database.Release import ReleaseArtifact
    from ..model.ReleaseScript import ReleaseScript, ReleaseScriptFile
    from ..model.RepositoryConfiguration import RepositoryConfiguration
    from ..model.Result import Result
    from ..services.ConfigurationService import ConfigurationService


class ReleaseContext(CommandContext, abc.ABC):
    """
    Abstract context for release step execution.
    
    Extends CommandContext with release-specific operations like progress tracking,
    artifact storage, and file downloading.
    """
    
    @property
    @abc.abstractmethod
    def release_script(self) -> "ReleaseScript":
        """Get the release script configuration."""
        ...
    
    @property
    @abc.abstractmethod
    def repo_config(self) -> "RepositoryConfiguration":
        """Get the repository configuration."""
        ...
    
    @property
    @abc.abstractmethod
    def working_dir(self) -> str:
        """Get the working directory for the release."""
        ...

    @property
    def gh(self) -> Optional["GitHub"]:
        """
        Get the GitHub API client, if available.

        This is only available in web contexts. CLI contexts return None.
        Release steps that require GitHub access should check this property
        and handle the case where it is None.

        :return: The GitHub API client or None.
        """
        return None

    @property
    def config_service(self) -> Optional["ConfigurationService"]:
        """
        Get the configuration service, if available.

        Only available in contexts that have access to the application
        configuration (e.g. web contexts). Returns None by default.
        Release steps that require it should check via accepts_context().

        :return: The configuration service or None.
        """
        return None

    @abc.abstractmethod
    def update_progress(
        self,
        *,
        position: Optional[Tuple[int, int]] = None,
        progress: Optional[float] = None,
        current_item: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Update the progress of the release step.
        
        :param position: A tuple indicating the current progress (current step, total steps).
        :param progress: A float indicating the progress percentage (0.0 to 1.0).
        :param current_item: Name or description of the current item being processed.
        :param message: Message to provide additional context about the progress.
        """
        ...

    @abc.abstractmethod
    def set_release_info(self, details: dict) -> None:
        """Update release information/metadata."""
        ...
    
    @abc.abstractmethod
    def set_release_result(self, result: "Result") -> None:
        """Set the result of the release step."""
        ...

    @abc.abstractmethod
    def next_release_step(self) -> None:
        """Advance to the next release step."""
        ...

    @abc.abstractmethod
    def download(self, file: str, local_name: Optional[str] = None) -> str:
        """
        Download a file from the repository.
        
        :param file: The file path in the repository.
        :param local_name: Optional local file path. If None, uses local_name(file).
        :return: The local file path.
        """
        ...

    @abc.abstractmethod
    def store_artifact(
        self,
        local_path: str,
        target_path: Optional[str] = None,
        kind: Optional[Literal["source", "intermediate", "final"]] = None,
        downloadable: bool = True,
    ) -> None:
        """
        Store an artifact produced by the release step.
        
        :param local_path: The local file path of the artifact.
        :param target_path: Optional target path for the artifact.
        :param kind: The type of artifact (source, intermediate, or final).
        :param downloadable: Whether the artifact should be downloadable.
        """
        ...

    def store_target_artifact(
        self,
        file: "ReleaseScriptFile",
        kind: Literal["source", "intermediate", "final"] = "final",
        downloadable: bool = True,
    ) -> None:
        """
        Store a target artifact based on a release script file.
        
        :param file: The release script file configuration.
        :param kind: The type of artifact (source, intermediate, or final).
        :param downloadable: Whether the artifact should be downloadable.
        """
        self.store_artifact(
            self.local_name(file.target.file),
            file.target.file,
            kind,
            downloadable,
        )

    @abc.abstractmethod
    def get_artifacts(self) -> List["ReleaseArtifact"]:
        """
        Get all artifacts produced by the release so far.
        
        :return: List of release artifacts.
        """
        ...

    def update_release(self, patch: dict) -> None:
        """
        Update release database fields directly.
        
        This is a low-level operation only available in web contexts.
        CLI contexts will ignore this call.
        
        :param patch: A dictionary of release fields to update.
        """
        pass  # No-op by default, web context overrides

    def raise_if_canceled(self) -> None:
        """
        Check if the release has been canceled and raise an exception if so.
        
        Should be called periodically during long-running operations.
        
        :raises ReleaseCanceledException: If the release has been canceled.
        """
        from .common import ReleaseCanceledException
        
        if self.canceled():
            raise ReleaseCanceledException("Release has been canceled!")

    def calculate_release_name(self) -> str:
        """
        Calculate a release name based on the current date.

        Subclasses should override this to check for existing releases.

        :return: A release name in the format vYYYY-MM-DD[.n].
        """
        from datetime import datetime
        return f"v{datetime.utcnow().strftime('%Y-%m-%d')}"

