import os.path
import shutil
from typing import Optional

from ose.commands.CommandContext import CommandContext


class CLICommandContext(CommandContext):
    def __init__(self, working_dir: Optional[str] = None):
        self._working_dir = working_dir if working_dir is not None else os.curdir

    def canceled(self) -> bool:
        return False

    def local_name(self, remote_name, file_ending=None) -> str:
        file_name = os.path.join(self._working_dir, remote_name)

        if file_ending is not None:
            return file_name[:file_name.rfind(".")] + file_ending

        return file_name

    def save_file(self, file: str, temporary: Optional[bool] = None, **kwargs):
        shutil.copy2(file, os.path.join(self._working_dir, os.path.basename(file)))
