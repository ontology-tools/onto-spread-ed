import os
from typing import List, Tuple, Set

from flask_sqlalchemy.query import Query

from onto_spread_ed.database.Release import Release
from onto_spread_ed.model.ReleaseScript import ReleaseScriptFile, ReleaseScript


def local_name(tmp: str, remote_name: str, file_ending=None) -> str:
    external_xlsx = os.path.join(tmp, os.path.basename(remote_name))

    if file_ending is not None:
        return external_xlsx[:external_xlsx.rfind(".")] + file_ending

    return external_xlsx


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


def order_sources(release_script: ReleaseScript) -> List[Tuple[str, ReleaseScriptFile]]:
    queue: List[Tuple[str, ReleaseScriptFile]] = []
    files: List[Tuple[str, ReleaseScriptFile]] = list(release_script.files.items())
    seen: Set[int] = set()
    while len(files) > 0:
        (k, file) = files.pop(0)
        if all(s.type == "owl" for s in file.sources):
            continue

        if all(n in (x for x, _ in queue) for n in file.needs):
            queue.append((k, file))
        else:
            files.append((k, file))

            if id(file) in seen:
                raise ValueError("Circular dependency in release files!")

            seen.add(id(file))

    return queue
