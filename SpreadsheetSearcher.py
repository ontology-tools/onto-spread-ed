import threading

from whoosh.qparser import MultifieldParser, QueryParser

from app import cache
from config import bucket
from index.BucketStorage import BucketStorage


class SpreadsheetSearcher:
    # bucket is defined in config.py
    def __init__(self):
        self.storage = BucketStorage(bucket)
        self.threadLock = threading.Lock()

    def searchFor(self, repo_name, search_string="", assigned_user=""):
        self.storage.open_from_bucket()
        ix = self.storage.open_index()

        mparser = MultifieldParser(["class_id","label","definition","parent","tobereviewedby"],
                                schema=ix.schema)

        query = mparser.parse("repo:"+repo_name+
                              (" AND ("+search_string+")" if search_string  else "")+
                              (" AND tobereviewedby:"+assigned_user if assigned_user else "") )

        with ix.searcher() as searcher:
            results = searcher.search(query, limit=100)
            resultslist = []
            for hit in results:
                allfields = {}
                for field in hit:
                    allfields[field]=hit[field]
                resultslist.append(allfields)

        ix.close()
        return (resultslist)

    def updateIndex(self, repo_name, folder, sheet_name, header, sheet_data):
        self.threadLock.acquire()
        print("Updating index...")
        self.storage.open_from_bucket()
        ix = self.storage.open_index()
        writer = ix.writer()
        mparser = MultifieldParser(["repo", "spreadsheet"],
                                   schema=ix.schema)
        print("About to delete for query string: ","repo:" + repo_name + " AND spreadsheet:'" + folder+"/"+sheet_name+"'")
        writer.delete_by_query(
            mparser.parse("repo:" + repo_name + " AND spreadsheet:\"" + folder+"/"+sheet_name+"\""))
        writer.commit()

        writer = ix.writer()

        for r in range(len(sheet_data)):
            row = [v for v in sheet_data[r].values()]
            del row[0] # Tabulator-added ID column

            if "ID" in header:
                class_id = row[header.index("ID")]
            else:
                class_id = None
            if "Label" in header:
                label = row[header.index("Label")]
            else:
                label = None
            if "Definition" in header:
                definition = row[header.index("Definition")]
            else:
                definition = None
            if "Parent" in header:
                parent = row[header.index("Parent")]
            else:
                parent = None
            if "To be reviewed by" in header:
                tobereviewedby = row[header.index("To be reviewed by")]
            else:
                tobereviewedby = None

            if class_id or label or definition or parent:
                writer.add_document(repo=repo_name,
                                    spreadsheet=folder+'/'+sheet_name,
                                    class_id=(class_id if class_id else None),
                                    label=(label if label else None),
                                    definition=(definition if definition else None),
                                    parent=(parent if parent else None),
                                    tobereviewedby=(tobereviewedby if tobereviewedby else None))
        writer.commit(optimize=True)
        self.storage.save_to_bucket()
        ix.close()
        self.threadLock.release()
        print("Update of index completed.")

    def getNextId(self,repo_name):
        self.threadLock.acquire()
        self.storage.open_from_bucket()
        ix = self.storage.open_index()

        nextId = 0

        mparser = QueryParser("class_id",
                              schema=ix.schema)
        if repo_name == "BCIO":
            updated_repo_name ="BCIO:" # in order to eliminate "BCIOR" from results
        else:
            updated_repo_name = repo_name
        query = mparser.parse(updated_repo_name.upper()+"*")
        # print("searching ", repo_name)
        with ix.searcher() as searcher:
            results = searcher.search(query, sortedby="class_id",reverse=True)
            tophit = results[0]
            mostRecentID = cache.get("latestID"+repo_name) # check latest ID
            if mostRecentID is None: # error check no cache set
                mostRecentID = 0
                print("error latestID",repo_name," was None!")
                cache.set("latestID"+repo_name, 0)
            nextId = int(tophit['class_id'].split(":")[1] )+1

            # check nextId against cached most recent id:
            if not(nextId > mostRecentID):
                print("cached version is higher: ", mostRecentID, " > ", nextId)
                nextId = cache.get("latestID"+repo_name)+1
            cache.set("latestID"+repo_name, nextId)


        ix.close()

        self.threadLock.release()
        return (nextId)
