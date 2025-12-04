import logging
import os.path
import shutil
import threading
from typing import Generator, Dict, List, Optional, Any

from flask_github import GitHub
from whoosh.qparser import MultifieldParser, QueryParser

from .index.FileStorage import FileStorage
from .index.create_index import add_entity_data_to_index, re_write_entity_data_set
from .index.schema import schema
from .services.ConfigurationService import ConfigurationService
from .utils.github import get_spreadsheet, get_spreadsheets


class SpreadsheetSearcher:
    _logger = logging.getLogger(__name__)

    def __init__(self, config: ConfigurationService, github: GitHub):
        self.config = config
        self.threadLock = threading.Lock()
        self.github = github

        index_dir = self.config.app_config["INDEX_PATH"]
        if not os.path.exists(index_dir):
            self._logger.info("Index directory not found. Creating it.")
            os.mkdir(index_dir)

        self.storage = FileStorage(index_dir)

        if not self.storage.index_exists():
            self._logger.info("Index not found. Creating it.")

            self.storage.create_index(schema)

    def search_for(self, repo_name, search_string="", assigned_user="", fields=None, limit: Optional[int] = 100):
        if fields is None:
            fields = ["class_id", "label", "definition", "parent", "tobereviewedby"]

        ix = self.storage.open_index()

        mparser = MultifieldParser(fields,
                                   schema=ix.schema)

        query = mparser.parse("repo:" + repo_name +
                              (" AND (" + search_string + ")" if search_string else "") +
                              (" AND tobereviewedby:" + assigned_user if assigned_user else ""))

        with ix.searcher() as searcher:
            results = searcher.search(query, limit=limit)
            resultslist = []
            for hit in results:
                allfields = {}
                for field in hit:
                    allfields[field] = hit[field]
                resultslist.append(allfields)

        ix.close()
        return resultslist

    def update_index(self, repo_name, path: str, sheet_data):
        self.threadLock.acquire()
        self._logger.debug("Update of index start")

        writer = None
        try:
            ix = self.storage.open_index()
            writer = ix.writer(timeout=60)  # Wait 60s for the writer lock
            mparser = MultifieldParser(["repo", "spreadsheet"],
                                       schema=ix.schema)
            self._logger.debug("About to delete for query string: " +
                               "repo:" + repo_name + " AND spreadsheet:'" + path + "'")
            writer.delete_by_query(
                mparser.parse("repo:" + repo_name + " AND spreadsheet:\"" + path + "\""))
            writer.commit()
            writer = ix.writer(timeout=60)  # Wait 60s for the writer lock

            for row in sheet_data:
                if "id" in row:
                    del row["id"]  # Tabulator-added ID column

                add_entity_data_to_index(row, repo_name, path, writer)

            writer.commit(optimize=True)

            self.storage.save()
            ix.close()
        finally:
            if writer is not None and not writer.is_closed:
                writer.cancel()

            self.threadLock.release()

        self._logger.debug("Update of index completed.")

    def get_next_id(self, repo_name):
        self.threadLock.acquire()
        ix = self.storage.open_index()

        mparser = QueryParser("class_id", schema=ix.schema)

        updated_repo_name = repo_name + ":"  # To avoid prefix matching issues (e.g., BCIO vs BCIOR)

        query = mparser.parse(updated_repo_name.upper() + "*")

        with ix.searcher() as searcher:
            results = searcher.search(query, sortedby="class_id", reverse=True)
            top_hit = next((hit['class_id'].split(":")[1] for hit in results), 0)
            next_id = int(top_hit) + 1

        ix.close()

        self.threadLock.release()
        return next_id

    def stats(self) -> Dict[str, Any]:

        self.threadLock.acquire()
        ix = self.storage.open_index()

        with ix.reader() as r:
            stats = dict(
                number_of_repositories=len(list(r.field_terms("repo"))),
                number_of_sheets=len(list(r.field_terms("spreadsheet"))),
                number_of_terms=r.doc_count(),
                repositories=list(r.field_terms("repo")),
                sheets=list(r.field_terms("spreadsheet"))

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

        try:
            index_dir = self.config.app_config['INDEX_PATH']
            shutil.rmtree(index_dir)
            os.mkdir(index_dir)
            index = self.storage.create_index(schema)
            repositories = self.config.loaded_repositories()

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
            for config in repositories:
                short_repo = config.short_name
                if repository_keys is not None and short_repo not in repository_keys:
                    continue

                branch = config.main_branch
                active_sheets = config.indexed_files
                regex = "|".join(f"({r})" for r in active_sheets)

                excel_files = get_spreadsheets(self.github, config.full_name, branch, include_pattern=regex)

                for file in excel_files:
                    _, data, _ = get_spreadsheet(self.github, config.full_name, file)

                    entity_data = data

                    spreadsheet = file
                    self._logger.debug(f"Rewriting entity data for repository '{short_repo} ({config.full_name})' "
                                       f"and file '{spreadsheet}'")
                    re_write_entity_data_set(short_repo, index, spreadsheet, entity_data)
                    sheets.append(f"{config.full_name}/{file}")

            self.storage.save()
            index.close()

        finally:
            self.threadLock.release()

        return sheets
