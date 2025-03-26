import os
from typing import List, Tuple, Dict

from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query

from ose.database.Release import Release, ReleaseArtifact
from ose.model.ReleaseScript import ReleaseScriptFile


def local_name(tmp: str, remote_name: str, file_ending=None) -> str:
    file_name = os.path.join(tmp, os.path.basename(remote_name))

    if file_ending is not None:
        return file_name[:file_name.rfind(".")] + file_ending

    return file_name


class ReleaseCanceledException(Exception):
    pass


def set_release_info(q: Query[Release], release_id: int, details) -> None:
    r = q.get(release_id)
    update_release(q, release_id, {Release.details: {**r.details, r.step: details}})


def update_release(q: Query[Release], release_id: int, patch: dict) -> None:
    q.filter(Release.id == release_id).update(patch)
    q.session.commit()


def next_release_step(q: Query[Release], release_id: int) -> None:
    return update_release(q, release_id, {Release.step: Release.step + 1})


def set_release_result(q, release_id, result):
    set_release_info(q, release_id, dict(
        errors=result.errors,
        warnings=result.warnings
    ))
    if not result.has_errors() and result.ok():
        next_release_step(q, release_id)
    else:
        update_release(q, release_id, dict(state="waiting-for-user"))


def order_sources(files: Dict[str, ReleaseScriptFile]) -> List[Tuple[str, ReleaseScriptFile]]:
    queue: List[Tuple[str, ReleaseScriptFile]] = []
    files: List[Tuple[str, ReleaseScriptFile]] = list(files.items())

    for k, file in files:
        unknown_dependencies = [n for n in file.needs if n not in (x for x, _ in files)]
        if any(unknown_dependencies):
            raise ValueError(f"Unknown dependencies '{', '.join(unknown_dependencies)}' for '{k}'")

    no_change_since = 0
    while len(files) > 0:
        (k, file) = files.pop(0)
        if all(s.type == "owl" for s in file.sources):
            no_change_since = 0
            continue

        if all(n in (x for x, _ in queue) for n in file.needs):
            queue.append((k, file))
            no_change_since = 0
        else:
            files.append((k, file))

            if len(files) < no_change_since:
                raise ValueError("Circular dependency in release files!")

            no_change_since += 1

    return queue


def add_artifact(db: SQLAlchemy, artifact: ReleaseArtifact) -> int:
    db.session.add(artifact)
    db.session.commit()

    return artifact.id


def get_artifacts(q: Query[ReleaseArtifact], release_id: int) -> List[ReleaseArtifact]:
    return q.filter_by(release_id=release_id).all()
