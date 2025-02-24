import json
from io import BytesIO
from typing import List

import openpyxl
import pyhornedowl
import requests
from flask_github import GitHub

import ose.utils.github as github
from ose.model.ReleaseScript import ReleaseScript
from ose.model.Result import Result
from ose.services.ConfigurationService import ConfigurationService
from ose.utils import str_space_eq, lower


def main(gh: GitHub, config: ConfigurationService, repo: str):
    result = Result([])
    repository = config.get(repo)
    release_script_json = config.get_file(repository, repository.release_script_path)
    release_script = ReleaseScript.from_json(json.loads(release_script_json))

    for source in release_script.external.sources:
        file = config.get_file_raw(repository, source.file)
        file = BytesIO(file)

        wb = openpyxl.load_workbook(file)
        sheet = wb.active
        rows = sheet.rows

        header = next(rows)
        iri_index = next((i for i, h in enumerate(header) if str_space_eq(lower(h.value), "purl")), None)
        version_index = next((i for i, h in enumerate(header) if str_space_eq(lower(h.value), "version")), None)
        id_index = next((i for i, h in enumerate(header) if str_space_eq(lower(h.value), "ontology id")), None)

        if None in [iri_index, version_index, id_index]:
            continue

        changes: List[str] = []
        for row in rows:
            id = row[id_index].value
            iri = row[iri_index].value

            if id in ["GAZ", "OPMI"]:  # GAZ is weird and crashes HornedOwl
                continue

            try:
                response = requests.get(iri)
                content = response.text

                serialisation = iri[iri.rfind(".") + 1:]
                onto = pyhornedowl.open_ontology_from_string(content, serialisation)

                version_iri = onto.get_version_iri()

                old_version = row[version_index].value
                if version_iri is None:
                    result.warning(type="no-version-iri",
                                   msg=f"Ontology '{id}' has no version IRI")
                else:
                    version_iri = str(version_iri)
                    if not str_space_eq(old_version, version_iri):
                        row[version_index].value = version_iri

                        changes.append(f"Updated '{id}' from {old_version} to {version_iri}")

            except Exception as e:
                result.error(type="load-ontology",
                             msg=f"Failed to load external ontology '{id}' from '{iri}'",
                             e=e)

        if len(changes) > 0:
            spreadsheet_stream = BytesIO()
            wb.save(spreadsheet_stream)

            github.save_file(gh, repository.full_name, source.file, spreadsheet_stream.getvalue(), "\n".join(changes),
                             repository.main_branch)

            result.value += changes

    return "\n".join(result.value)
