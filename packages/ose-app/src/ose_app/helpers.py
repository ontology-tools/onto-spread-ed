"""
Logic shared between the JSON API routes.
"""
from urllib.parse import quote
from typing import Any, Dict, List, Optional

from flask import current_app, g
from flask_github import GitHub

from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.utils.github import get_branches


def visible_repositories(config: ConfigurationService) -> Dict[str, Any]:
    """Repositories (short name -> project) the current user can see."""
    user_name = g.user.github_login if g.user else "*"
    user_repos = (config.app_config['USERS']
                  .get(user_name, config.app_config['USERS'].get("*", {}))
                  .get("repositories", []))

    repositories = {s: config.get(s) for s in user_repos}
    return {k: v for k, v in repositories.items() if v is not None}


def user_initials(config: ConfigurationService) -> str:
    login = g.user.github_login
    users = config.app_config['USERS']
    if login in users:
        return users[login].get("initials", login[0:2])

    current_app.logger.info(f"The user {login} has no known metadata")
    return login[0:2]


def all_initials(config: ConfigurationService) -> List[Optional[str]]:
    return [v.get("initials") for v in config.app_config["USERS"].values() if "initials" in v]


def filter_tree_entries(items: List[dict]) -> List[Dict[str, str]]:
    """Flat directories and .xlsx files from a git trees response; hides dot-entries and `scripts` directories."""
    entries = []
    for item in items:
        parts = item["path"].split("/")
        if any(p.startswith(".") for p in parts) or "scripts" in (parts if item["type"] == "tree" else parts[:-1]):
            continue
        if item["type"] == "tree":
            entries.append(dict(path=item["path"], type="dir"))
        elif item["type"] == "blob" and ".xlsx" in parts[-1]:
            entries.append(dict(path=item["path"], type="file"))
    return entries


def repo_tree(github: GitHub, config: ConfigurationService, repo_key: str,
              branch: Optional[str] = None) -> Optional[dict]:
    """Whole tree of a branch, shown on the repository browsing page. Returns None for unknown repositories."""
    repository = config.get(repo_key)
    if repository is None:
        return None

    active_branch = branch or repository.main_branch
    branches = get_branches(github, repository.full_repository_name)
    result = github.get(f'repos/{repository.full_repository_name}/git/trees/{quote(active_branch, safe="")}',
                        params={"recursive": 1})

    return dict(
        repo_name=repo_key,
        full_name=repository.full_repository_name,
        branches=branches,
        active_branch=active_branch,
        main_branch=repository.main_branch,
        entries=filter_tree_entries(result.get("tree", [])),
        truncated=bool(result.get("truncated")),  # ponytail: huge repos are cut off by GitHub, not paged through
    )


def is_up_to_date(github: GitHub, config: ConfigurationService, repo_key: str, folder: str, spreadsheet: str,
                  old_sha: str, branch: Optional[str] = None) -> bool:
    repository = config.get(repo_key)
    params = {"ref": branch} if branch else {}
    spreadsheet_file = github.get(f'repos/{repository.full_repository_name}/contents/{folder}/{spreadsheet}',
                                  params=params)
    return old_sha == spreadsheet_file['sha']


if __name__ == "__main__":
    fake = [
        {"path": "a", "type": "tree"}, {"path": "a/b.xlsx", "type": "blob"}, {"path": "a/c.txt", "type": "blob"},
        {"path": ".github", "type": "tree"}, {"path": ".github/w.xlsx", "type": "blob"},
        {"path": "scripts", "type": "tree"}, {"path": "scripts/x.xlsx", "type": "blob"},
        {"path": "a/sub", "type": "tree"}, {"path": "a/sub/.hidden.xlsx", "type": "blob"},
        {"path": "top.xlsx", "type": "blob"},
    ]
    assert filter_tree_entries(fake) == [
        {"path": "a", "type": "dir"}, {"path": "a/b.xlsx", "type": "file"},
        {"path": "a/sub", "type": "dir"}, {"path": "top.xlsx", "type": "file"},
    ]
    print("ok")
