from .ReleaseStep import ReleaseStep
from ..model.Result import Result


class ImportExternalWithGitHubActionsReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "IMPORT_EXTERNAL_WITH_GITHUB_ACTIONS"

    def run(self) -> bool:
        result = Result(())

        # TODO: Trigger the GitHub Actions workflow that builds the external ontology

        file = self._release_script.external

        self._download(file.target.file)

        self.store_target_artifact(file, downloadable=False)

        self._set_release_result(result)
        return result.ok()
