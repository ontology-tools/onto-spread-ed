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

        upload_queue = [a for a in artifacts if a.kind == "final"]
        self._total_items = len(upload_queue)
        for artifact in upload_queue:
            self._next_item(item=artifact.target_path, message="Uploading")
            with open(artifact.local_path, "rb") as f:
                content = f.read()
                github.save_file(self._gh, self._release_script.full_repository_name, artifact.target_path, content,
                                 f"Release {artifact.target_path}.", branch)
            sleep(1)  # Wait a second to avoid rate limit
            self._raise_if_canceled()

        self._update_progress(message="Creating pull request and release")
        release_body = f"Released version '{release_name}' of {self._release_script.short_repository_name}"
        pr_nr = github.create_pr(self._gh, self._release_script.full_repository_name,
                                 title=f"Release {release_name}",
                                 body=release_body,
                                 source=branch,
                                 target=config.main_branch)
        self._raise_if_canceled()

        github.merge_pr(self._gh, self._release_script.full_repository_name, pr_nr, "squash")
        github.create_release(self._gh, self._release_script.full_repository_name, release_name, branch)

        return True
