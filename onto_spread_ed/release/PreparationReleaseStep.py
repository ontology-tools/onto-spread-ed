from .ReleaseStep import ReleaseStep
from ..utils import download_file


class PreparationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "PREPARATION"

    def run(self):
        for source in self._release_script.external.sources:
            external_xlsx = self._local_name(source.file)
            download_file(self._gh, self._release_script.full_repository_name, source.file, external_xlsx)

        self._raise_if_canceled()

        for file in self._release_script.files.values():
            for source in file.sources:
                if source.type == "owl":
                    continue

                xlsx = self._local_name(source.file)
                download_file(self._gh, self._release_script.full_repository_name, source.file, xlsx)

            self._raise_if_canceled()

        self._next_release_step()

        return True
