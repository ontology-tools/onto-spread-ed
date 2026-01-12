import json
from io import BytesIO
from typing import Annotated, List

from injector import inject
import openpyxl
import pyhornedowl
import requests
from flask_github import GitHub

from ose.model.Script import Script
import ose.utils.github as github
from ose.model.ReleaseScript import ReleaseScript
from ose.model.Result import Result
from ose.services.ConfigurationService import ConfigurationService
from ose.utils import str_space_eq, lower

class UpdateImportsToLatestVersionsScript(Script):
    @property
    def id(self) -> str:
        return "update-imports-to-latest-versions"

    @property
    def title(self) -> str:
        return "Update Imports to Latest Versions"

    @inject
    def __init__(self, gh: GitHub, config: ConfigurationService) -> None:
        self.gh = gh
        self.config = config

    def run(self, repo: Annotated[str, "Repository name"]) -> str:
        result = Result([])
        repository = self.config.get(repo)
        
        assert repository is not None, f"Repository configuration for '{repo}' not found."
        
        release_script_json = self.config.get_file(repository, repository.release_script_path)
        
        assert release_script_json is not None, f"Release script not found at '{repository.release_script_path}'"
        
        release_script = ReleaseScript.from_json(json.loads(release_script_json))

        for source in release_script.external.sources:
            file = self.config.get_file_raw(repository, source.file)
            assert file is not None, f"Could not load file '{source.file}' from repository '{repository.full_name}'"
            file = BytesIO(file)

            wb = openpyxl.load_workbook(file)
            sheet = wb.active
            
            assert sheet is not None, f"Could not load active sheet from '{source.file}'"
            
            rows = sheet.rows

            header = next(rows)
            iri_index = next((i for i, h in enumerate(header) if
                            str_space_eq(lower(str(h.value)), "purl") or str_space_eq(lower(str(h.value)), "iri")), None)
            version_index = next((i for i, h in enumerate(header) if str_space_eq(lower(str(h.value)), "version")), None)
            id_index = next((i for i, h in enumerate(header) if str_space_eq(lower(str(h.value)), "ontology id")), None)

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

                github.save_file(self.gh, repository.full_name, source.file, spreadsheet_stream.getvalue(), "\n".join(changes),
                                repository.main_branch)

                result.value += changes

        return "\n".join(result.value)
