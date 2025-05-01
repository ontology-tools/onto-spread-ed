import csv
from typing import Tuple, List, Literal

from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy

from .ReleaseStep import ReleaseStep
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScript
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..services.RobotOntologyBuildService import RobotOntologyBuildService


class ImportExternalWithGitHubActionsReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "IMPORT_EXTERNAL_WITH_GITHUB_ACTIONS"

    def run(self) -> bool:
        result = Result(())

        # Trigger the GitHub Actions workflow that builds the external ontology



        file = self._release_script.external

        self._download(file.target.file)

        self.store_target_artifact(file, downloadable=False)

        self._set_release_result(result)
        return result.ok()
