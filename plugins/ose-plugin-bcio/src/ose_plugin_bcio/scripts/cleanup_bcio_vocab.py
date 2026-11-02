import re
import base64
import io
import json

import aiohttp
from github import Github
from injector import inject

from ose.ontology.ExcelOntology import ExcelOntology
from ose_app.model.Script import Script
from ose.schema import termid
from ..BCIOSearchService import BCIOSearchService
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.utils.github import get_spreadsheets, get_spreadsheet


class CleanUpBCIOVocabScript(Script):
    @property
    def id(self) -> str:
        return "cleanup-bcio-vocab"

    @property
    def title(self) -> str:
        return "Cleanup terms on BCIO Vocab"

    @inject
    def __init__(self, gh: Github, config: ConfigurationService) -> None:
        super().__init__()
        self.gh = gh
        self.config = config

    async def run(self) -> str:
        repo = self.config.get("BCIO")

        assert repo is not None, "BCIO repository configuration not found."

        # get all BCIO Vocab terms
        async with aiohttp.ClientSession() as session:
            service = BCIOSearchService(repo.prefixes, session)
            bcio_terms = await service.get_all_terms()

        bcio_vocab_by_id = dict([(t.id.strip(), t) for t in bcio_terms if t.id is not None])

        # get all BCIO excel terms
        branch = repo.main_branch
        active_sheets = [source.file for file in repo.files.values() for source in file.sources
                         if source.type in ("classes", "relations")]
        regex = "|".join(f"({re.escape(r)})" for r in active_sheets) or r"(?!)"

        excel_files = get_spreadsheets(self.gh, repo.full_repository_name, branch, include_pattern=regex)

        for file in excel_files:
            _, data, _ = get_spreadsheet(self.gh, repo.full_repository_name, file)

            for entity in data:
                term_id = entity.get("ID", "").strip()
                if term_id in bcio_vocab_by_id:
                    del bcio_vocab_by_id[term_id]

        exclude = set()
        for k, v in bcio_vocab_by_id.items():
            # Population is expanded
            if v.get_relation_value(termid(id=None, label="lowerLevelOntology")) == "population":
                exclude.add(k)

            if v.curation_status() == "external":
                exclude.add(k)

        for k in exclude:
            del bcio_vocab_by_id[k]

        with open("ids.json", "w") as f:
            json.dump(bcio_vocab_by_id, f)

        excel_ontology = ExcelOntology("tmp://tmp")
        for t in bcio_vocab_by_id.values():
            excel_ontology.add_term(t)

        excel = excel_ontology.to_excel()
        excel.save("to_be_deleted.xlsx")

        stream = io.BytesIO()
        excel.save(stream)

        # stream to base64
        b64content = base64.b64encode(stream.getvalue()).decode()

        return (
            f"The entities in this excel sheet have been identified to be deleted. "
            f'<a download="to_be_deleted.xlsx" href="data:application/vnd.ms-excel;base64,{b64content}>'
            f"to_be_deleted.xlsx</a>"
        )
