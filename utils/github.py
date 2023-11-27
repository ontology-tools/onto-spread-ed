import base64
import csv
import io
import logging
import re
from typing import List, Tuple, Dict, Optional, Union

import openpyxl
from flask_github import GitHub

_logger = logging.getLogger(__name__)


def get_csv(github: GitHub, repository_name: str, folder: str, spreadsheet_name: str) -> Tuple[
    str, List[List[str]], List[str]]:
    csv_file = github.get(
        f'repos/{repository_name}/contents/{folder}/{spreadsheet_name}'
    )
    file_sha = csv_file['sha']
    csv_content = csv_file['content']
    # print(csv_content)
    decoded_data = str(base64.b64decode(csv_content), 'utf-8')
    # print(decoded_data)
    csv_reader = csv.reader(io.StringIO(decoded_data))
    csv_data = list(csv_reader)
    header = csv_data[0]
    rows = csv_data[1:]

    return file_sha, rows, header


def get_spreadsheet(github: GitHub,
                    repository_name: str,
                    folder: str,
                    spreadsheet: str) -> Tuple[str, List[Dict[str, str]], List[str]]:
    spreadsheet_file = github.get(
        f'repos/{repository_name}/contents/{folder}/{spreadsheet}'
    )
    file_sha = spreadsheet_file['sha']
    base64_bytes = spreadsheet_file['content'].encode('utf-8')
    decoded_data = base64.decodebytes(base64_bytes)
    wb = openpyxl.load_workbook(io.BytesIO(decoded_data))
    sheet = wb.active

    header = [cell.value for cell in sheet[1] if cell.value]
    rows = []
    try:
        for row in sheet[2:sheet.max_row]:
            values = {}
            for key, cell in zip(header, row):
                values[key] = cell.value
            if any(values.values()):
                rows.append(values)

    except Exception as e:
        _logger.error(f"Could not index {spreadsheet}: {e}")

    return file_sha, rows, header


def get_spreadsheets(github: GitHub,
                     repository_name: str,
                     folder: str = "",
                     exclude_pattern: Optional[Union[re.Pattern, str]] = None,
                     include_pattern: Optional[Union[re.Pattern, str]] = None) -> list[str]:
    tree = github.get(
        f'repos/{repository_name}/git/trees/master',
        params={"recursive": "true"}
    )
    entries = tree["tree"]

    return [x["path"] for x in entries if x["path"].endswith(".xlsx") and
            (re.match(include_pattern, x["path"])
             if include_pattern is not None else
             not (exclude_pattern and re.match(exclude_pattern, x["path"])))
            ]
