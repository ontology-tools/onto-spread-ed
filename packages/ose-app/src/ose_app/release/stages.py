import logging
import shutil
from datetime import datetime
from functools import cached_property
from os import path
from pathlib import Path
from typing import Callable

import git
from github import Auth, Github
from pydantic import Field

from ose.building import (
    BuildContext,
    BuildStage,
    Progress,
    ProgressManager,
    StageResult,
)
from ose.result import ResultContext, with_result_context_method
from ose.utils.asyncio import as_thread
from ose.utils.logging import log_prefix

from ose_app.utils.git import git_env

_logger = logging.getLogger(__name__)


class ReleaseContext(BuildContext):
    github_token: str = Field(exclude=True, repr=False)
    """The token of the user running the release. Never persisted, it is provided whenever the release runs."""

    created_branches: set[str] = set()

    @cached_property
    def gh(self) -> Github:
        return Github(auth=Auth.Token(self.github_token))

    def build_branch_name(self) -> str:
        return f"build/{self.build_id}"

    def git_env(self, with_author: bool = False) -> dict[str, str]:
        if not with_author:
            return git_env(self.github_token)

        user = self.gh.get_user()
        return git_env(self.github_token, user.name or user.login, f"{user.id}+{user.login}@users.noreply.github.com")


ReleaseStage = BuildStage[ReleaseContext]


def _worktrees(repo: git.Repo) -> list[str]:
    return [
        path.realpath(line.removeprefix("worktree "))
        for line in repo.git.worktree("list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]


class PreparationStage(ReleaseStage):
    @classmethod
    def name(cls) -> str:
        return "PREPARATION"

    @with_result_context_method
    async def run(
        self,
        ctx: ResultContext,
        on_progress_update: Callable[[Progress], None] | None = None,
    ) -> tuple[()]:
        with log_prefix(_logger, str(self.context.build_id), self.name()):
            await self._prepare()
            return ()

    @as_thread
    def _prepare(self) -> None:
        build_dir, branch = self.context.build_dir, self.context.build_branch_name()
        repo = git.Repo(self.context.project_dir)
        repo.git.fetch("origin", "--prune", env=self.context.git_env())

        if path.realpath(build_dir) in _worktrees(repo):
            _logger.debug(f"Worktree {build_dir} already exists, removing it")
            repo.git.worktree("remove", "--force", build_dir)

        _logger.debug(f"Creating a worktree for {self.context.project_dir} at {build_dir} with branch `{branch}`")
        repo.git.worktree("add", "-B", branch, build_dir, f"origin/{self.project.main_branch}")
        self.context.created_branches.add(branch)


class HumanVerificationStage(ReleaseStage):
    @classmethod
    def name(cls) -> str:
        return "HUMAN_VERIFICATION"

    @with_result_context_method
    async def run(
        self,
        ctx: ResultContext,
        on_progress_update: Callable[[Progress], None] | None = None,
    ) -> StageResult:
        files = [{"artifact": str(a.id), "name": a.final_path} for a in self.context.final_artifacts()]

        return "paused", {"files": files}


class GithubPublishStage(ReleaseStage):
    @classmethod
    def name(cls) -> str:
        return "GITHUB_PUBLISH"

    @with_result_context_method
    async def run(
        self,
        ctx: ResultContext,
        on_progress_update: Callable[[Progress], None] | None = None,
    ) -> tuple[()]:
        repo = self.project.full_repository_name
        main_branch = self.project.main_branch
        branch_name = f"release/{datetime.now().astimezone().strftime('%Y-%m-%d_%H-%M-%S')}"
        gh = self.context.gh

        final_artifacts = self.context.final_artifacts()
        progress = ProgressManager(on_progress_update, len(final_artifacts) + 1)

        for a in final_artifacts:
            assert a.final_path is not None  # final_artifacts() only returns artifacts with a final path

            progress.next_item(item=a.final_path, message="Copying")

            src = path.abspath(path.join(self.context.build_dir, a.local_path))
            dst = path.abspath(path.join(self.context.build_dir, a.final_path))
            if src != dst:
                _logger.debug(f"Copying {src} to {dst}")
                Path(dst).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)

        release_name = await self._release_name(gh, repo)

        progress.update(message="Committing and pushing changes")
        await self._commit_and_push(branch_name, f"Release {release_name}", {a.final_path for a in final_artifacts})
        self.context.created_branches.add(branch_name)

        progress.next_item(message="Creating pull request and release")
        release_body = f"Released version '{release_name}' of {self.project.short_repository_name}"
        pr_nr = await self._create_pr(gh, repo, f"Release {release_name}", release_body, branch_name, main_branch)

        await self._merge_pr(gh, repo, pr_nr, "squash")

        await self._create_release(gh, repo, release_name, main_branch)

        return ()

    @as_thread
    def _commit_and_push(self, branch_name: str, message: str, final_paths: set[str | None]) -> None:
        git_repo = git.Repo(self.context.build_dir)

        dirty_files = set(item.a_path for item in git_repo.index.diff(None)) | set(git_repo.untracked_files)
        if dirty_files - final_paths:
            _logger.warning(f"Dirty files in the worktree that are not final artifacts: {dirty_files - final_paths}")

        git_repo.git.checkout("-b", branch_name)
        git_repo.git.add(".")
        git_repo.git.commit("-m", message, env=self.context.git_env(with_author=True))
        git_repo.git.push("origin", branch_name, env=self.context.git_env())

    @staticmethod
    @as_thread
    def _release_name(gh: Github, repo: str) -> str:
        """Release names follow the format vYYYY-MM-DD[.1,2,3...]"""
        release_name = f"v{datetime.now().astimezone().strftime('%Y-%m-%d')}"
        releases = gh.get_repo(repo).get_releases()
        last_release = releases.get_page(0)[0] if releases.totalCount > 0 else None
        if last_release is not None and last_release.name.startswith(release_name):
            _logger.info(f"Release {release_name} already exists.")

            if "." in last_release.name:
                release_name += f".{int(last_release.name.split('.')[-1]) + 1}"
            else:
                release_name += ".1"
        return release_name

    @staticmethod
    @as_thread
    def _create_pr(gh: Github, repo: str, title: str, body: str, source: str, target: str) -> int:
        response = gh.get_repo(repo).create_pull(title=title, body=body, head=source, base=target)
        return response.number

    @staticmethod
    @as_thread
    def _create_release(gh: Github, repo: str, release_name: str, target: str) -> None:
        gh.get_repo(repo).create_git_release(
            tag=release_name,
            name=release_name,
            message=f"Release {release_name}",
            draft=False,
            prerelease=False,
            target_commitish=target,
        )

    @staticmethod
    @as_thread
    def _merge_pr(gh: Github, repo: str, pr_nr: int, merge_method: str = "squash") -> None:
        pr = gh.get_repo(repo).get_pull(pr_nr)

        message = f"{pr.title}\n\n{pr.body}".strip()
        pr.merge(merge_method=merge_method, commit_message=message)


class CleanupStage(ReleaseStage):
    """Removes the worktree of the release and deletes the branches it created, locally and on GitHub"""

    @classmethod
    def name(cls) -> str:
        return "CLEANUP"

    @with_result_context_method
    async def run(
        self,
        ctx: ResultContext,
        on_progress_update: Callable[[Progress], None] | None = None,
    ) -> tuple[()]:
        await self._cleanup(ctx)
        return ()

    @as_thread
    def _cleanup(self, ctx: ResultContext) -> None:
        repo = git.Repo(self.context.project_dir)
        build_dir = self.context.build_dir

        if path.realpath(build_dir) in _worktrees(repo):
            repo.git.worktree("remove", "--force", build_dir)
        repo.git.worktree("prune")

        remote_branches = {ref.remote_head for ref in repo.remotes.origin.refs}
        for branch in self.context.created_branches:
            if branch in repo.heads:
                repo.git.branch("-D", branch)
            if branch in remote_branches:
                try:
                    repo.git.push("origin", "--delete", branch, env=self.context.git_env())
                except git.GitCommandError as e:
                    ctx.log.warning(type="branch-not-deleted", branch=branch, msg=str(e))


__all__ = [
    "CleanupStage",
    "GithubPublishStage",
    "HumanVerificationStage",
    "PreparationStage",
    "ReleaseContext",
    "ReleaseStage",
]
