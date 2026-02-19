import logging

from .ReleaseStep import ReleaseStep


class HumanVerificationReleaseStep(ReleaseStep):
    _logger = logging.getLogger(__name__)

    @classmethod
    def name(cls) -> str:
        return "HUMAN_VERIFICATION"

    def run(self) -> bool:
        artifacts = [a for a in self._artifacts() if a.kind == "final"]

        if self._context.gh is not None:
            # Web context: present download links and pause for human approval
            from flask import url_for

            files = [{
                "link": url_for(".download_release_file", file=a.id,
                                repo=self._release_script.short_repository_name),
                "name": a.target_path
            } for a in artifacts]

            self._set_release_info(dict(ok=False, files=files))
            self._update_release(dict(state="waiting-for-user"))

            return False
        else:
            # Non-web context: log artifacts and auto-approve
            self._logger.info("Release artifacts for verification:")
            for a in artifacts:
                self._logger.info(f"  {a.target_path}")
            self._logger.info("Auto-approving release (non-interactive context).")
            return True
