from flask import url_for

from .ReleaseStep import ReleaseStep


class HumanVerificationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "HUMAN_VERIFICATION"

    def run(self) -> bool:
        files = [{
            "link": url_for(".download_release_file", file=a.id,
                            repo=self._release_script.short_repository_name),
            "name": a.target_path
        } for a in self._artifacts() if a.kind == "final"]

        self._set_release_info(dict(
            ok=False,
            files=files
        ))
        self._update_release(dict(state="waiting-for-user"))

        return False
