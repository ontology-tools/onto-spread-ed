from __future__ import annotations

import base64
import io
import logging
import re
from typing import List, Tuple, Dict, Optional, Literal, Union

import openpyxl
from github import Github, GithubException, UnknownObjectException
from github.GithubObject import NotSet
from github.GitRelease import GitRelease

_logger = logging.getLogger(__name__)


def is_unauthorized(e: BaseException) -> bool:
    return isinstance(e, GithubException) and e.status == 401


def download_file(github: Github, repository_name: str, spreadsheet: str, outpath: str, branch: Optional[str] = None):
    content = get_file(github, repository_name, spreadsheet, branch=branch)

    with open(outpath, "wb") as f:
        f.write(content)


def get_content(github: Github, repository_name: str, path: str, branch: Optional[str] = None) -> Tuple[str, bytes]:
    """The sha and the content of a file. Raises `GithubException` if it cannot be read."""
    repo = github.get_repo(repository_name)
    file = repo.get_contents(path, ref=branch or NotSet)
    if isinstance(file, list):
        raise IsADirectoryError(f"'{path}' in '{repository_name}' is a directory")

    if file.encoding == "base64":
        return file.sha, file.decoded_content

    # GitHub omits the content of files larger than 1 MB. Blobs are available up to 100 MB.
    return file.sha, base64.b64decode(repo.get_git_blob(file.sha).content)


def get_file(github: Github, repository_name: str, spreadsheet: str, branch: Optional[str] = None) -> bytes:
    return get_content(github, repository_name, spreadsheet, branch)[1]


def parse_spreadsheet(data: bytes) -> Tuple[List[Dict[str, str]], List[str]]:
    wb = openpyxl.load_workbook(io.BytesIO(data))
    sheet = wb.active

    header = [cell.value for cell in sheet[1] if cell.value]
    rows = []
    row_iterator = sheet.rows
    next(row_iterator)  # Skip header
    for row in row_iterator:
        values = {}
        for key, cell in zip(header, row):
            values[key] = cell.value
        if any(values.values()):
            rows.append(values)

    return rows, header


def get_spreadsheet(github: Github,
                    repository_name: str,
                    path: str,
                    branch: Optional[str] = None) -> Tuple[str, List[Dict[str, str]], List[str]]:
    file_sha, data = get_content(github, repository_name, path, branch)
    rows, header = parse_spreadsheet(data)

    return file_sha, rows, header


def get_spreadsheets(github: Github,
                     repository_name: str,
                     branch: str,
                     exclude_pattern: Optional[Union[re.Pattern, str]] = None,
                     include_pattern: Optional[Union[re.Pattern, str]] = None) -> list[str]:
    tree = github.get_repo(repository_name).get_git_tree(branch, recursive=True)

    return [x.path for x in tree.tree if x.path.endswith(".xlsx") and
            (re.match(include_pattern, x.path)
             if include_pattern is not None else
             not (exclude_pattern and re.match(exclude_pattern, x.path)))
            ]


def create_branch(github: Github, repo: str, branch: str, parent_branch: str) -> None:
    repository = github.get_repo(repo)
    sha = repository.get_git_ref(f"heads/{parent_branch}").object.sha
    repository.create_git_ref(f"refs/heads/{branch}", sha)


def delete_branch(github: Github, repo: str, branch: str) -> None:
    github.get_repo(repo).get_git_ref(f"heads/{branch}").delete()


def merge_branch(github: Github, repo: str, head: str, base: str, commit_message: str) -> None:
    """Merges `head` into `base` directly, without a pull request"""
    github.get_repo(repo).merge(base=base, head=head, commit_message=commit_message)


def save_file(github: Github, repo: str, path: str, content: bytes, message: str, branch: str,
              sha: Optional[str] = None) -> None:
    """
    Creates or overwrites the file. With `sha`, GitHub refuses the change (409) if the file changed after it had that
    sha.
    """
    repository = github.get_repo(repo)

    if sha is None:
        # Check if the file already exists
        try:
            existing = repository.get_contents(path, ref=branch)
            if not isinstance(existing, list):
                sha = existing.sha
        except UnknownObjectException:
            pass

    if sha is None:
        repository.create_file(path, message, content, branch=branch)
    else:
        repository.update_file(path, message, content, sha, branch=branch)


def create_pr(github: Github, repo: str, title: str, body: str, source: str, target: str) -> int:
    return github.get_repo(repo).create_pull(title=title, body=body, head=source, base=target).number


def merge_pr(github: Github, repo: str, pr: int, merge_method: Literal['squash', 'merge', 'rebase'] = "squash") -> None:
    github.get_repo(repo).get_pull(pr).merge(merge_method=merge_method)


def get_latest_release(gh: Github, full_repository_name: str) -> Optional[GitRelease]:
    try:
        return gh.get_repo(full_repository_name).get_latest_release()
    except UnknownObjectException:
        return None


def create_release(gh: Github, full_repository_name: str, tag_name: str, branch: str):
    gh.get_repo(full_repository_name).create_git_release(
        tag=tag_name,
        name=tag_name,
        message=f"Release {tag_name}",
        target_commitish=branch,
    )


def get_branches(gh: Github, full_repository_name: str) -> list[str]:
    return [b.name for b in gh.get_repo(full_repository_name).get_branches()]
