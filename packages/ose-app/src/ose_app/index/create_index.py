import logging

from whoosh.index import FileIndex
from whoosh.qparser import MultifieldParser # pyright: ignore[reportPrivateImportUsage]
from whoosh.writing import IndexWriter

from ose.project import Project

_logger = logging.getLogger(__name__)

EntityData = dict[str, str]


def indexed_files(project: Project) -> list[str]:
    """The spreadsheets whose terms are indexed, i.e. every spreadsheet source of the project"""
    return list(dict.fromkeys(
        s.file for f in [project.external, *project.files.values()] for s in f.sources if s.type != "owl"
    ))



def re_write_entity_data_set(repo_name: str, index: FileIndex, sheet_name: str, entity_data: list[EntityData]):
    writer = index.writer(timeout=60)  # Wait 60s for the writer lock
    mparser = MultifieldParser(["repo", "spreadsheet"],
                               schema=index.schema)
    writer.delete_by_query(mparser.parse("repo:" + repo_name + " AND spreadsheet:" + sheet_name))
    writer.commit()
    writer = index.writer(timeout=60)  # Wait 60s for the writer lock
    for data in entity_data:
        add_entity_data_to_index(data, repo_name, sheet_name, writer)

    writer.commit(optimize=True)


def add_entity_data_to_index(entity_data: EntityData, repo_name: str, sheet_name: str, writer: IndexWriter):
    rowdata = entity_data

    if 'Curation status' in entity_data and str(entity_data["Curation status"]) == "Obsolete":
        _logger.info(f"Not adding obsolete entity '{entity_data.get('ID')}' to index")
        return

    if "ID" in rowdata:
        class_id = rowdata["ID"]
    else:
        class_id = None
    if "Label" in rowdata:
        label = rowdata["Label"]
    else:
        label = None
    if "Definition" in rowdata:
        definition = rowdata["Definition"]
    else:
        definition = None
    if "Parent" in rowdata:
        parent = rowdata["Parent"]
    else:
        parent = None
    if "To be reviewed by" in rowdata:
        to_be_reviewed_by = rowdata["To be reviewed by"]
    else:
        to_be_reviewed_by = None

    if class_id or label or definition or parent:
        _logger.debug(
            f"Adding entity data '{entity_data.get('ID')}' to index for repository '{repo_name}'"
            f"and sheet '{sheet_name}'")

        writer.add_document(repo=repo_name,
                            spreadsheet=sheet_name,
                            class_id=(class_id if class_id else None),
                            label=(label if label else None),
                            definition=(definition if definition else None),
                            parent=(parent if parent else None),
                            tobereviewedby=(to_be_reviewed_by if to_be_reviewed_by else None))
