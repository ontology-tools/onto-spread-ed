from .ReleaseStep import ReleaseStep


class PreparationReleaseStep(ReleaseStep):
    @classmethod
    def name(cls) -> str:
        return "PREPARATION"

    def run(self):
        total = len(self._release_script.external.sources)
        if self._release_script.external.addParentsFile is not None:
            total += 1
        if self._release_script.external.renameTermFile is not None:
            total += 1
        for file in self._release_script.files.values():
            total += sum(1 for source in file.sources if source.type != "owl")
            if file.addParentsFile is not None:
                total += 1
            if file.renameTermFile is not None:
                total += 1

        self._total_items = total

        for source in self._release_script.external.sources:
            self._next_item(item=source.file, message="Downloading")
            self._download(source.file)

        self._raise_if_canceled()

        if self._release_script.external.addParentsFile is not None:
            self._next_item(item=self._release_script.external.addParentsFile, message="Downloading")
            self._download(self._release_script.external.addParentsFile)

        self._raise_if_canceled()

        if self._release_script.external.renameTermFile is not None:
            self._next_item(item=self._release_script.external.renameTermFile, message="Downloading")
            self._download(self._release_script.external.renameTermFile)

        self._raise_if_canceled()

        for file in self._release_script.files.values():
            for source in file.sources:
                if source.type == "owl":
                    continue

                self._next_item(item=source.file, message="Downloading")
                self._download(source.file)

                self._raise_if_canceled()

            if file.addParentsFile is not None:
                self._next_item(item=file.addParentsFile, message="Downloading")
                self._download(file.addParentsFile)

            self._raise_if_canceled()

            if file.renameTermFile is not None:
                self._next_item(item=file.renameTermFile, message="Downloading")
                self._download(file.renameTermFile)

            self._raise_if_canceled()

        self._next_release_step()

        return True
