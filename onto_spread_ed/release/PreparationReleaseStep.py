from .ReleaseStep import ReleaseStep


class PreparationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "PREPARATION"

    def run(self):
        for source in self._release_script.external.sources:
            self._download(source.file)

        self._raise_if_canceled()

        if self._release_script.external.addParentsFile is not None:
            self._download(self._release_script.external.addParentsFile)

        self._raise_if_canceled()

        if self._release_script.external.renameTermFile is not None:
            self._download(self._release_script.external.renameTermFile)

        self._raise_if_canceled()

        for file in self._release_script.files.values():
            for source in file.sources:
                if source.type == "owl":
                    continue

                self._download(source.file)

                self._raise_if_canceled()

            if file.addParentsFile is not None:
                self._download(file.addParentsFile)

            self._raise_if_canceled()

            if file.renameTermFile is not None:
                self._download(file.renameTermFile)

            self._raise_if_canceled()

        self._next_release_step()

        return True
