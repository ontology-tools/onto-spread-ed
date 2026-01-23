from typing import Optional, Literal

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Query

from .CommandContext import CommandContext
from ..database.Release import Release, ReleaseArtifact
from ..model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ..release.common import add_artifact, local_name
from ..services.ConfigurationService import ConfigurationService


class ReleaseCommandContext(CommandContext):
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

    def canceled(self) -> bool:
        r: Release = self._q.get(self._release_id)
        return r.state == "canceled"

    def local_name(self, remote_name, file_ending=None) -> str:
        return local_name(self._working_dir, remote_name, file_ending)

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

    def save_file(self, file: str, temporary: Optional[bool] = None, **kwargs):
        return self.store_artifact(file, kind="intermediate" if temporary else "final", **kwargs)
