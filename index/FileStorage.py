import whoosh.filedb.filestore

from index.ExtendedStorage import ExtendedStorage


class FileStorage(ExtendedStorage, whoosh.filedb.filestore.FileStorage):
    pass