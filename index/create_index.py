import io
import logging
from typing import List, Tuple, Union, Dict

import openpyxl
from whoosh.index import FileIndex
from whoosh.qparser import MultifieldParser
from whoosh.writing import SegmentWriter

_logger = logging.getLogger(__name__)

EntityData = Tuple[List, List]
"""
Combines a header with data
"""


def to_entity_data(data: Union[Dict[str, str]]) -> EntityData:
    if isinstance(data, dict):
        return list(data.keys()), list(data.values())


def to_entity_data_list(raw: Union[List[Dict[str, str]]]) -> List[EntityData]:
    return [to_entity_data(x) for x in raw]


def parse_input_sheet(file: Union[str, bytes, io.BytesIO]) -> List[EntityData]:
    """
    Parses a given Excel file to pairs of headers and data

    The first line of the Excel file is interpreted as header. All following lines are combined with this header and
    returned.

    :param file: The Excel file. Either a filename or bytes of the Excel file
    :return: Pairs of headers and data
    """
    if isinstance(file, bytes):
        file = io.BytesIO(file)

    wb = openpyxl.load_workbook(file)

    sheet = wb.active
    data = sheet.rows

    header = [i.value for i in next(data)]

    return [(header, [i.value for i in row]) for row in data]


def re_write_entity_data_set(repo_name: str, index: FileIndex, sheet_name: str, entity_data: List[EntityData]):
    writer = index.writer()
    mparser = MultifieldParser(["repo", "spreadsheet"],
                               schema=index.schema)
    writer.delete_by_query(mparser.parse("repo:" + repo_name + " AND spreadsheet:" + sheet_name))
    writer.commit()
    writer = index.writer()
    for data in entity_data:
        add_entity_data_to_index(data, repo_name, sheet_name, writer)

    writer.commit(optimize=True)


def add_entity_data_to_index(entity_data: EntityData, repo_name: str, sheet_name: str, writer: SegmentWriter):
    header, rowdata = entity_data

    _logger.debug(f"Adding entity data '{entity_data[1][0]}' to index for repository '{repo_name}' and sheet '{sheet_name}'")

    if "ID" in header:
        class_id = rowdata[header.index("ID")]
    else:
        class_id = None
    if "Label" in header:
        label = rowdata[header.index("Label")]
    else:
        label = None
    if "Definition" in header:
        definition = rowdata[header.index("Definition")]
    else:
        definition = None
    if "Parent" in header:
        parent = rowdata[header.index("Parent")]
    else:
        parent = None
    if "To be reviewed by" in header:
        to_be_reviewed_by = rowdata[header.index("To be reviewed by")]
    else:
        to_be_reviewed_by = None
    if class_id or label or definition or parent:
        writer.add_document(repo=repo_name,
                            spreadsheet=sheet_name,
                            class_id=(class_id if class_id else None),
                            label=(label if label else None),
                            definition=(definition if definition else None),
                            parent=(parent if parent else None),
                            tobereviewedby=(to_be_reviewed_by if to_be_reviewed_by else None))
