import whoosh.filedb.filestore

from .ExtendedStorage import ExtendedStorage


class FileStorage(ExtendedStorage, whoosh.filedb.filestore.FileStorage):
    pass
