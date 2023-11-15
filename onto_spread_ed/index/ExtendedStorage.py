import whoosh.filedb.filestore


class ExtendedStorage(whoosh.filedb.filestore.Storage):
    def load(self) -> None:
        pass

    def save(self) -> None:
        pass