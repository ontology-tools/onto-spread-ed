import logging

from ose.release.ReleaseContext import ReleaseContext

from .ReleaseStep import ReleaseStep


class HumanVerificationReleaseStep(ReleaseStep):
    _logger = logging.getLogger(__name__)

    @classmethod
    def name(cls) -> str:
        return "HUMAN_VERIFICATION"
    
    @classmethod
    def accepts_context(cls, context: ReleaseContext) -> bool:
        return context.gh is not None

    def run(self) -> bool:
        artifacts = [a for a in self._artifacts() if a.kind == "final"]
        
        from flask import url_for

        files = [{
            "link": url_for(".download_release_file", file=a.id,
                            repo=self._release_script.short_repository_name),
            "name": a.target_path
        } for a in artifacts]

        self._set_release_info(dict(ok=False, files=files))
        self._update_release(dict(state="waiting-for-user"))

        return False
