import logging

import whoosh.filedb.filestore

from index.ExtendedStorage import ExtendedStorage


# Implementation of Google Cloud Storage for index
class BucketStorage(ExtendedStorage, whoosh.filedb.filestore.RamStorage):
    _logger = logging.getLogger(__name__)

    def __init__(self, bucket):
        super().__init__()
        self.bucket = bucket
        self.filenameslist = []

    def open(self) -> None:
        self.open_from_bucket()

    def save(self) -> None:
        self.save_to_bucket()

    def save_to_bucket(self):
        for name in self.files.keys():
            with self.open_file(name) as source:
                self._logger.debug("Saving file %s", name)
                blob = self.bucket.blob(name)
                blob.upload_from_file(source)
        for name in self.filenameslist:
            if name not in self.files.keys():
                blob = self.bucket.blob(name)
                self._logger.debug("Deleting old file %s", name)
                self.bucket.delete_blob(blob.name)
                self.filenameslist.remove(name)

    def open_from_bucket(self):
        self.filenameslist = []
        for blob in self.bucket.list_blobs():
            self._logger.debug("Opening blob", blob.name)
            self.filenameslist.append(blob.name)
            f = self.create_file(blob.name)
            blob.download_to_file(f)
            f.close()
