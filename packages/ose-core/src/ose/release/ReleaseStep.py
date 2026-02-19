import abc
import logging
import os
from typing import Tuple, Optional, Literal, List, TYPE_CHECKING

from .ReleaseContext import ReleaseContext
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ..model.RepositoryConfiguration import RepositoryConfiguration
from ..model.Result import Result

if TYPE_CHECKING:
    from ..database.Release import ReleaseArtifact


class ReleaseStep(abc.ABC):
    """
    Abstract base class for release steps.
    
    Release steps perform specific operations as part of the release process.
    They use a ReleaseContext to interact with their execution environment
    (CLI or Web), allowing the same step implementation to be used in both.
    """
    
    _logger = logging.getLogger(__name__)

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Return the unique name of this release step."""
        ...

    _context: ReleaseContext
    _total_items: Optional[int] = None
    _current_item: int = 1

    def __init__(self, context: ReleaseContext) -> None:
        """
        Initialize a release step with a context.

        :param context: The release context providing access to files, artifacts, and progress tracking.
        """
        self._context = context

    @classmethod
    def accepts_context(cls, context: ReleaseContext) -> bool:
        """
        Check whether this step can run in the given context.

        Steps that require specific context capabilities (e.g. GitHub access)
        should override this to return False when those capabilities are missing.

        :param context: The release context to check.
        :return: True if this step can run in the given context.
        """
        return True

    @property
    def _release_script(self) -> ReleaseScript:
        """Get the release script from the context."""
        return self._context.release_script

    @property
    def _working_dir(self) -> str:
        """Get the working directory from the context."""
        return self._context.working_dir

    @property
    def _repo_config(self) -> RepositoryConfiguration:
        """Return the repository configuration for the current release script."""
        return self._context.repo_config

    def _update_progress(self,
                         *,
                         position: Optional[Tuple[int, int]] = None,
                         progress: Optional[float] = None,
                         current_item: Optional[str] = None,
                         message: Optional[str] = None):
        """
        Update the progress of the release step.
        
        :param position: A tuple indicating the current progress (current step, total steps).
        :param progress: A float indicating the progress percentage (0.0 to 1.0). Calculated from position if None.
        :param current_item: Name or description of the current item being processed.
        :param message: Message to provide additional context about the progress.
        """
        self._context.update_progress(
            position=position,
            progress=progress,
            current_item=current_item,
            message=message,
        )

    def _next_item(self, *, item: Optional[str] = None, message: Optional[str] = None):
        """
        Update the progress to the next item. Requires `self._total_items` to be set.
        
        :param item: Name or description of the current item being processed.
        :param message: Message to provide additional context about the progress.
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
        Check if the release has been canceled and raise an exception if so. 
        Should be called periodically during long-running operations.
        """
        self._context.raise_if_canceled()

    def _local_name(self, remote_name, file_ending=None) -> str:
        """
        Get the local path for a downloaded remote file name.
        
        :param remote_name: The remote file name or path.
        :param file_ending: Optional file ending to replace.
        :return: The local file path corresponding to the remote file.
        """
        return self._context.local_name(remote_name, file_ending)

    def _set_release_info(self, details) -> None:
        """Update release information/metadata."""
        self._context.set_release_info(details)

    def _next_release_step(self) -> None:
        """Advance to the next release step."""
        self._context.next_release_step()

    def _update_release(self, patch: dict) -> None:
        """Update release database fields directly (web contexts only)."""
        self._context.update_release(patch)

    def _set_release_result(self, result):
        """Set the result of the release step."""
        self._context.set_release_result(result)

    def _download(self, file: str, local_name: Optional[str] = None):
        """
        Download a file from the repository.
        
        :param file: The file path in the repository.
        :param local_name: Optional local file path.
        :return: The local file path.
        """
        return self._context.download(file, local_name)

    def _store_artifact(self, local_path: str, target_path: Optional[str] = None,
                       kind: Optional[Literal["source", "intermediate", "final"]] = None,
                       downloadable: bool = True) -> None:
        """Store an artifact produced by the release step."""
        self._context.store_artifact(local_path, target_path, kind, downloadable)

    def _store_target_artifact(self, file: ReleaseScriptFile,
                              kind: Literal["source", "intermediate", "final"] = "final",
                              downloadable: bool = True):
        """Store a target artifact based on a release script file."""
        self._context.store_target_artifact(file, kind, downloadable)

    def _artifacts(self) -> List["ReleaseArtifact"]:
        """Get all artifacts produced by the release so far."""
        return self._context.get_artifacts()

    def _load_externals_ontology(self) -> Result[ExcelOntology]:
        """Load the externals ontology from the OWL file."""
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
        """Calculate a release name based on the current date."""
        return self._context.calculate_release_name()
