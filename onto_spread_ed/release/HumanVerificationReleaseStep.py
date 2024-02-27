from flask import url_for

from .ReleaseStep import ReleaseStep


class HumanVerificationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "HUMAN_VERIFICATION"

    def run(self) -> bool:
        files = [{
            "link": url_for(".download_release_file", file=f.target.file),
            "name": f.target.file
        } for k, f in self._release_script.files.items()]

        self._set_release_info(dict(
            ok=False,
            files=files
        ))
        self._update_release(dict(state="waiting-for-user"))

        return False
