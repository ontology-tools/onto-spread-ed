from datetime import datetime
from time import sleep

from .ReleaseStep import ReleaseStep
from ..utils import github


class GithubPublishReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "GITHUB_PUBLISH"

    def run(self) -> bool:
        config = self._config.get(self._release_script.full_repository_name)
        branch = f"release/{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}"
        github.create_branch(self._gh, self._release_script.full_repository_name, branch,
                             config.main_branch)
        self._raise_if_canceled()

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

        release_month = datetime.utcnow().strftime('%B %Y')
        release_body = f"Released the {release_month} version of {self._release_script.short_repository_name}"
        pr_nr = github.create_pr(self._gh, self._release_script.full_repository_name,
                                 title=f"{release_month} Release",
                                 body=release_body,
                                 source=branch,
                                 target=config.main_branch)
        self._raise_if_canceled()

        github.merge_pr(self._gh, self._release_script.full_repository_name, pr_nr, "squash")
        self._raise_if_canceled()

        return True
