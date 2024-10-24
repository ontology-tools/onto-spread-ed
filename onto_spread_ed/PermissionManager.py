from typing import Dict, Set, Optional

from flask import g

PERMISSION_IMPLICATIONS: Dict[str, Set[str]] = {
    "admin": set(),
    "view": set(),
    "edit": {"view"},
    "add-external-ontology": {"edit"},
    "release": {"edit"},
    "index": {"view"},
    "hierarchical-spreadsheets": {"view"},
    "repository-config-view": {"view"},
    "repository-config-manage-loaded": {"repository-config-view"},
    "repository-config-manage-startup": {"repository-config-view"},
    "scripts": {"edit"},
}


class PermissionManager:
    _group_permissions: Dict[str, Set[str]]
    _user_permissions: Dict[str, Set[str]]
    _user_repos: Dict[str, Set[str]]

    def __init__(self, config):
        self._group_permissions = {k: self.expand_permissions(set(v["permissions"])) for k, v in
                                   config["PERMISSION_GROUPS"].items()}

        user_permissions = {
            name: set.union(set(user.get("permissions", [])),
                            *(self._group_permissions[g] for g in user.get("groups", [])))
            for name, user in config["USERS"].items()
        }
        self._user_permissions = {name: self.expand_permissions(p) for name, p in user_permissions.items()}

        self._user_repos = {
            name: set(user.get("repositories", []))
            for name, user in config["USERS"].items()
        }

    def expand_permissions(self, permissions: Set[str]) -> Set[str]:
        """
        Applies implication rules
        """

        expanded = set.union(permissions, *[PERMISSION_IMPLICATIONS[p] for p in permissions])

        if expanded == permissions:
            return expanded

        return self.expand_permissions(expanded)

    def user_permission(self, username: str) -> Set[str]:
        return self._user_permissions.get(username, self._user_permissions.get("*", set()))

    def has_permissions(self, user_name: str, *permissions: str, repository: Optional[str] = None) -> bool:
        user_permission = self.user_permission(user_name)
        user_repos = self._user_repos.get(user_name, {})

        if "admin" in user_permission:
            return True

        return all(p in user_permission for p in permissions) and (repository is None or repository in user_repos)

    def current_user_has_permissions(self, *permissions: str, repository: Optional[str] = None) -> bool:
        """
        Checks whether the currently requesting user has specific permissions.
        Note: This requires an application context e.g. from a request
        """
        if not g.user:
            return False

        user_name = g.user.github_login if g.user else "*"
        return self.has_permissions(user_name, *permissions, repository=repository)
