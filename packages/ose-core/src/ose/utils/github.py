from __future__ import annotations

import base64
import csv
import io
import logging
import re
from typing import List, Tuple, Dict, Optional, Literal, Union

import openpyxl
from flask_github import GitHub, GitHubError

_logger = logging.getLogger(__name__)


def get_csv(github: GitHub,
            repository_name: str,
            folder: str,
            spreadsheet_name: str,
            branch: Optional[str] = None) -> Tuple[str, List[List[str]], List[str]]:
    params = {"ref": branch} if branch else {}
    csv_file = github.get(
        f'repos/{repository_name}/contents/{folder}/{spreadsheet_name}',
        params=params
    )
    file_sha = csv_file['sha']
    csv_content = csv_file['content']
    # print(csv_content)
    decoded_data = str(base64.b64decode(csv_content), 'utf-8')
    # print(decoded_data)
    csv_reader = csv.reader(io.StringIO(decoded_data))
    csv_data = list(csv_reader)
    header = csv_data[0]
    rows = csv_data[1:]

    return file_sha, rows, header


def download_file(github: GitHub, repository_name: str, spreadsheet: str, outpath: str, branch: Optional[str] = None):
    content = get_file(github, repository_name, spreadsheet, branch=branch)

    with open(outpath, "wb") as f:
        f.write(content)


def get_file(github: GitHub, repository_name: str, spreadsheet: str, branch: Optional[str] = None) -> bytes:
    params = {"ref": branch} if branch else {}
    response = github.get(
        f'repos/{repository_name}/contents/{spreadsheet}',
        headers={
            "Accept": "application/vnd.github.raw+json"
        },
        params=params
    )
    return response.content


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


def get_spreadsheet(github: GitHub,
                    repository_name: str,
                    path: str,
                    branch: Optional[str] = None) -> Tuple[str, List[Dict[str, str]], List[str]]:
    params = {"ref": branch} if branch else {}
    spreadsheet_file = github.get(
        f'repos/{repository_name}/contents/{path}',
        params=params
    )
    file_sha = spreadsheet_file['sha']
    base64_bytes = spreadsheet_file['content'].encode('utf-8')
    decoded_data = base64.decodebytes(base64_bytes)

    rows, header = parse_spreadsheet(decoded_data)

    return file_sha, rows, header


def get_spreadsheets(github: GitHub,
                     repository_name: str,
                     branch: str,
                     exclude_pattern: Optional[Union[re.Pattern, str]] = None,
                     include_pattern: Optional[Union[re.Pattern, str]] = None) -> list[str]:
    tree = github.get(
        f'repos/{repository_name}/git/trees/{branch}',
        params={"recursive": "true"}
    )
    entries = tree["tree"]

    return [x["path"] for x in entries if x["path"].endswith(".xlsx") and
            (re.match(include_pattern, x["path"])
             if include_pattern is not None else
             not (exclude_pattern and re.match(exclude_pattern, x["path"])))
            ]


def create_branch(github: GitHub, repo: str, branch: str, parent_branch: str) -> None:
    response = github.get(f"repos/{repo}/git/ref/heads/{parent_branch}")
    if not response or "object" not in response or "sha" not in response["object"]:
        raise Exception(f"Unable to get SHA for HEAD of {parent_branch} in {repo}")
    sha = response["object"]["sha"]
    # current_app.logger.debug("About to try to create branch in %s", f"repos/{repo_detail}/git/refs")
    response = github.post(
        f"repos/{repo}/git/refs", data={"ref": f"refs/heads/{branch}", "sha": sha},
    )
    if not response:
        raise Exception(f"Unable to create new branch {branch} in {repo}")


def save_file(github: GitHub, repo: str, path: str, content: bytes, message: str, branch: str) -> None:
    data = dict(
        message=message,
        branch=branch,
        content=base64.b64encode(content).decode("ascii")
    )

    # Check if the file already exists
    try:
        response = github.get(
            f'repos/{repo}/contents/{path}?ref={branch}'
        )
        data["sha"] = response["sha"]
    except GitHubError as e:
        if e.response.status_code != 404 and not e.response.ok:
            raise e

    github.put(f"repos/{repo}/contents/{path}", data=data)


def create_pr(github: GitHub, repo: str, title: str, body: str, source: str, target: str) -> int:
    response = github.post(
        f"repos/{repo}/pulls",
        data={
            "title": title,
            "head": source,
            "base": target,
            "body": body
        },
    )

    return response['number']


def merge_pr(github: GitHub, repo: str, pr: int, merge_method: Literal['squash', 'merge', 'rebase'] = "squash") -> None:
    github.put(f"repos/{repo}/pulls/{pr}/merge", data=dict(
        merge_method=merge_method
    ))


def get_latest_release(gh: GitHub, full_repository_name: str) -> Optional[Dict[str, str]]:
    try:
        response = gh.get(f"repos/{full_repository_name}/releases/latest")
        return response
    except GitHubError as e:
        if e.response.status_code == 404:
            return None
        else:
            raise e


def create_release(gh: GitHub, full_repository_name: str, tag_name: str, branch: str):
    data = dict(
        tag_name=tag_name,
        target_commitish=branch,
        name=tag_name,
        body=f"Release {tag_name}"
    )

    gh.post(f"repos/{full_repository_name}/releases", data=data)

def get_branches(gh: GitHub, full_repository_name: str) -> list[str]:
    branches = gh.get(f"repos/{full_repository_name}/branches")
    return [b["name"] for b in branches]
