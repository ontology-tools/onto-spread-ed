import logging
import os.path
import shutil
import threading
from typing import Generator, Dict, List, Optional, Any

from flask_caching import Cache
from flask_github import GitHub
from whoosh.qparser import MultifieldParser, QueryParser

from .index.FileStorage import FileStorage
from .index.create_index import add_entity_data_to_index, to_entity_data_list, re_write_entity_data_set
from .index.schema import schema
from .utils.github import get_spreadsheet


class SpreadsheetSearcher:
    _logger = logging.getLogger(__name__)

    def __init__(self, cache: Cache, config: Dict, github: GitHub):
        self.config = config
        self.threadLock = threading.Lock()
        self.cache = cache
        self.github = github

        index_dir = config["INDEX_PATH"]
        if not os.path.exists(index_dir):
            self._logger.info("Index directory not found. Creating it.")
            os.mkdir(index_dir)

        self.storage = FileStorage(index_dir)

        if not self.storage.index_exists():
            self._logger.info("Index not found. Creating it.")

            self.storage.create_index(schema)


    def search_for(self, repo_name, search_string="", assigned_user=""):
        # self.storage.open_from_bucket()
        ix = self.storage.open_index()

        mparser = MultifieldParser(["class_id", "label", "definition", "parent", "tobereviewedby"],
                                   schema=ix.schema)

        query = mparser.parse("repo:" + repo_name +
                              (" AND (" + search_string + ")" if search_string else "") +
                              (" AND tobereviewedby:" + assigned_user if assigned_user else ""))

        with ix.searcher() as searcher:
            results = searcher.search(query, limit=100)
            resultslist = []
            for hit in results:
                allfields = {}
                for field in hit:
                    allfields[field] = hit[field]
                resultslist.append(allfields)

        ix.close()
        return resultslist

    def update_index(self, repo_name, folder, sheet_name, header, sheet_data):
        self.threadLock.acquire()
        self._logger.debug("Update of index start")
        # self.storage.open_from_bucket()
        ix = self.storage.open_index()
        writer = ix.writer()
        mparser = MultifieldParser(["repo", "spreadsheet"],
                                   schema=ix.schema)
        self._logger.debug("About to delete for query string: " +
              "repo:" + repo_name + " AND spreadsheet:'" + folder + "/" + sheet_name + "'")
        writer.delete_by_query(
            mparser.parse("repo:" + repo_name + " AND spreadsheet:\"" + folder + "/" + sheet_name + "\""))
        writer.commit()
        writer = ix.writer()

        for r in range(len(sheet_data)):
            row = [v for v in sheet_data[r].values()]
            del row[0]  # Tabulator-added ID column

            add_entity_data_to_index((header, row), repo_name, folder + '/' + sheet_name, writer)

        writer.commit(optimize=True)

        self.storage.save()
        ix.close()
        self.threadLock.release()

        self._logger.debug("Update of index completed.")

    def get_next_id(self, repo_name):
        self.threadLock.acquire()
        ix = self.storage.open_index()

        mparser = QueryParser("class_id",
                              schema=ix.schema)
        if repo_name == "BCIO":
            updated_repo_name = "BCIO:"  # in order to eliminate "BCIOR" from results
        else:
            updated_repo_name = repo_name
        query = mparser.parse(updated_repo_name.upper() + "*")
        # print("searching ", repo_name)
        with ix.searcher() as searcher:
            results = searcher.search(query, sortedby="class_id", reverse=True)
            top_hit = results[0]
            most_recent_id = self.cache.get("latestID" + repo_name)  # check latest ID
            if most_recent_id is None:  # error check no cache set
                most_recent_id = 0
                print("error latestID", repo_name, " was None!")
                self.cache.set("latestID" + repo_name, 0)
            next_id = int(top_hit['class_id'].split(":")[1]) + 1

            # check nextId against cached most recent id:
            if not (next_id > most_recent_id):
                print("cached version is higher: ", most_recent_id, " > ", next_id)
                next_id = self.cache.get("latestID" + repo_name) + 1
            self.cache.set("latestID" + repo_name, next_id)

        ix.close()

        self.threadLock.release()
        return next_id

    def stats(self) -> dict[str, Any]:
        stats = dict()

        self.threadLock.acquire()
        ix = self.storage.open_index()

        with ix.reader() as r:
            stats = dict(
                sheets=r.doc_count(),
                entities=len(list(r.all_terms()))
            )

        ix.close()

        self.threadLock.release()

        return stats


    def rebuild_index(self, repository_keys: Optional[List[str]] = None) -> List[str]:
        """
        Rebuild the index for entity data stored in Excel files.

        If not list of keys is given, all repositories the current user has access to are indexed.

        :param repository_keys: List of short names of the repositories to index
        :return: Names of sheets that have been indexed in the form `repository/file`
        """
        self.threadLock.acquire()

        index_dir = self.config["INDEX_PATH"]
        shutil.rmtree(index_dir)
        os.mkdir(index_dir)
        index = self.storage.create_index(schema)
        repositories = self.config["REPOSITORIES"]

        def get_excel_files(repo, directory="") -> Generator[str, None, None]:

            directories = self.github.get(
                f'repos/{repo}/contents/{directory}'
            )

            for entry in directories:
                if entry['type'] == 'dir':
                    yield from get_excel_files(repo, entry['path'])
                elif entry['type'] == 'file' and entry['name'].endswith('.xlsx'):
                    yield entry['path']

        sheets = []
        for repository_key, repository in repositories.items():
            if repository_keys is not None and repository_key not in repository_keys:
                continue

            excel_files = get_excel_files(repository)

            for file in excel_files:
                _, data, _ = get_spreadsheet(self.github, repository, "", file)

                entity_data = to_entity_data_list(data)

                spreadsheet = file
                self._logger.debug(f"Rewriting entity data for repository '{repository_key} ({repository})' and file '{spreadsheet}'")
                re_write_entity_data_set(repository_key, index, spreadsheet, entity_data)
                sheets.append(f"{repository}/{file}")

        self.storage.save()
        index.close()
        self.threadLock.release()

        return sheets

