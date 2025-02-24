import asyncio
import base64
import io
import json

import aiohttp
from flask_github import GitHub

from ose.model.ExcelOntology import ExcelOntology
from ose.model.TermIdentifier import TermIdentifier
from ose.search_api.BCIOSearchService import BCIOSearchService
from ose.services.ConfigurationService import ConfigurationService
from ose.utils import get_spreadsheets, get_spreadsheet


def main(gh: GitHub, config: ConfigurationService, repo: str):
    repo = config.get("BCIO")

    async def inner():
        # get all BCIO Vocab terms
        async with aiohttp.ClientSession() as session:
            service = BCIOSearchService(config, session)

            bcio_terms = await service.get_all_terms()

        bcio_vocab_by_id = dict([(t.id.strip(), t) for t in bcio_terms if t.id is not None])

        # get all BCIO excel terms
        branch = repo.main_branch
        active_sheets = repo.indexed_files
        regex = "|".join(f"({r})" for r in active_sheets)

        excel_files = get_spreadsheets(gh, repo.full_name, branch, include_pattern=regex)

        for file in excel_files:
            _, data, _ = get_spreadsheet(gh, repo.full_name, file)

            for entity in data:
                term_id = entity.get("ID", "").strip()
                if term_id in bcio_vocab_by_id:
                    del bcio_vocab_by_id[term_id]

        exclude = set()
        for k, v in bcio_vocab_by_id.items():
            # Population is expanded
            if v.get_relation_value(TermIdentifier(id=None, label="lowerLevelOntology")) == "population":
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

        return (f'The entities in this excel sheet have been identified to be deleted. '
                f'<a download="to_be_deleted.xlsx" href="data:application/vnd.ms-excel;base64,{b64content}>'
                f'to_be_deleted.xlsx</a>')

    return asyncio.run(inner())
