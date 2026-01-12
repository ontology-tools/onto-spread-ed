import logging
import os.path
import shutil
from tempfile import TemporaryDirectory
from typing import Optional

from ose_core.commands.CommandContext import CommandContext


class CLICommandContext(CommandContext):
    _logger = logging.getLogger(__name__)

    _working_dir: str
    _tempdir: Optional[TemporaryDirectory] = None

    def __init__(self, working_dir: Optional[str] = None):
        if working_dir is None:
            self._tempdir = TemporaryDirectory("ose-cli-context")
            self._working_dir = self._tempdir.name
        else:
            self._working_dir = os.path.abspath(working_dir)

    def canceled(self) -> bool:
        return False

    def local_name(self, remote_name, file_ending=None) -> str:
        file_name = os.path.join(self._working_dir, remote_name)

        if file_ending is not None:
            file_name = file_name[:file_name.rfind(".")] + file_ending

        self._logger.debug(f"Local name of '{remote_name}' is '{file_name}' (ending: {file_ending})")

        return file_name

    def save_file(self, file: str, temporary: Optional[bool] = None, **kwargs):
        target_path = os.path.abspath(os.path.join(self._working_dir, file))

        if os.path.abspath(target_path) != os.path.abspath(file):
            self._logger.debug(f"Saving file '{file}' to '{target_path}'")
            shutil.copy2(file, target_path)
        else:
            self._logger.debug(f"Saving file '{file}' to '{target_path}' (Already existing)")

    def cleanup(self) -> None:
        super().cleanup()

        if self._tempdir is not None:
            self._tempdir.cleanup()
