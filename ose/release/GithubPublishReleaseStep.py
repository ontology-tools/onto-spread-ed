import logging
from datetime import datetime
from time import sleep

from .ReleaseStep import ReleaseStep
from ..utils import github


class GithubPublishReleaseStep(ReleaseStep):
    _logger = logging.getLogger(__name__)

    @classmethod
    def name(cls) -> str:
        return "GITHUB_PUBLISH"

    def run(self) -> bool:
        config = self._config.get(self._release_script.full_repository_name)
        branch = f"release/{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}"
        github.create_branch(self._gh, self._release_script.full_repository_name, branch,
                             config.main_branch)
        self._raise_if_canceled()

        release_name = self._calculate_release_name()


        artifacts = self.artifacts()

        files = [a.target_path for a in artifacts]
        self._total_items = len(files)
        for file in files:
            self._next_item(item=file, message="Uploading")
            with open(self._local_name(file), "rb") as f:
                content = f.read()
                github.save_file(self._gh, self._release_script.full_repository_name, file, content,
                                 f"Release {file}.", branch)
            sleep(1)  # Wait a second to avoid rate limit
            self._raise_if_canceled()

        release_body = f"Released version '{release_name}' of {self._release_script.short_repository_name}"
        pr_nr = github.create_pr(self._gh, self._release_script.full_repository_name,
                                 title=f"Release {release_name}",
                                 body=release_body,
                                 source=branch,
                                 target=config.main_branch)
        self._raise_if_canceled()

        github.merge_pr(self._gh, self._release_script.full_repository_name, pr_nr, "squash")
        github.create_release(self._gh, self._release_script.full_repository_name, release_name, branch)
        self._raise_if_canceled()

        return True
