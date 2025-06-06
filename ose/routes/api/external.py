import base64
import io
import json
import os
from typing import List
from urllib import parse

import flask
import jsonschema
import openpyxl
import requests
from flask import jsonify, Blueprint, request, current_app, Response
from flask_github import GitHub
from openpyxl.worksheet.worksheet import Worksheet

from ose.guards.with_permission import requires_permissions
from ose.model.ExcelOntology import OntologyImport
from ose.model.TermIdentifier import TermIdentifier
from ose.services.ConfigurationService import ConfigurationService
from ose.utils import github, str_empty

bp = Blueprint("api_external", __name__, url_prefix="/api/external")


@bp.route("/guess-parent", methods=["POST"])
@requires_permissions("view")
def guess_parent():
    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "req_body_guess_parent.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    try:
        term = TermIdentifier(**data.get("term"))
        parent = TermIdentifier(**data.get("parent"))
        [prefix, id] = term.id.split(":")

        # Try to get the term from OLS. Then get the parent from there.
        response = requests.get(f"https://www.ebi.ac.uk/ols4/api/ontologies/{prefix}/terms?short_form={prefix}:{id}")

        if not response.ok:
            # Not found. Just search for the term
            response = requests.get("https://www.ebi.ac.uk/ols4/api/v2/entities", params={
                "search": parent.label,
                "lang": "en",
                "exactMatch": "false",
                "includeObsoleteEntities": "false"
            })

            guesses = [dict(ontology_id=e.get("definedBy", e["curie"].split(":"))[0],
                            purl=e.get("ontologyIri", None),
                            term=TermIdentifier(id=e["curie"], label=next(iter(e["label"])))) for e in
                       response.json()["elements"]]
            guesses = [g for g in guesses if
                       not str_empty(g['ontology_id']) and g['ontology_id'].lower() != prefix.lower()]

            return jsonify(guesses)

        data = response.json()
        term_iri = next((x["iri"] for x in data["_embedded"]["terms"] if x["obo_id"] == f"{prefix}:{id}"), None)

        if not term_iri:
            return jsonify(None)

        response = requests.get(f"https://www.ebi.ac.uk/ols4/api/v2/ontologies/{prefix.lower()}/" +
                                f"classes/{parse.quote(parse.quote(term_iri, safe=''))}")

        if not response.ok:
            return jsonify(None)

        ols_term = response.json()
        parent_iri = ols_term["directParent"]
        parent_ols = ols_term["linkedEntities"][parent_iri]
        guesses = [dict(
            term=TermIdentifier(id=parent_ols["curie"], label=parent_ols["label"]),
            purl=parent_ols.get("ontologyIri", None),
            ontology_id=parent_ols["curie"].split(":")[0],
        )]

        guesses = [g for g in guesses if not str_empty(g['ontology_id']) and g['ontology_id'].lower() != prefix.lower()]

        for g in guesses:
            if "label" in g:
                g["label"] = next(iter(g["label"]))

        return jsonify(guesses)
    except Exception as e:
        current_app.logger.error(f"Error guessing parent: {e}")
        return jsonify(None)


@bp.route("/<repo>/import", methods=["POST"])
@requires_permissions("edit")
def import_term(repo: str, gh: GitHub, config: ConfigurationService):
    user_name = flask.g.user.github_login if flask.g.user else "*"
    user_repos = (config.app_config['USERS']
                  .get(user_name, config.app_config['USERS'].get("*", {}))
                  .get("repositories", []))

    if repo not in user_repos:
        return jsonify({"msg": f"No such repository '{repo}'"}), 404

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "req_body_import.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    repository = config.get(repo)

    import_ontology_id = data.get("ontologyId")
    import_purl = data.get("purl", f"http://purl.obolibrary.org/obo/{import_ontology_id.lower()}.owl")
    import_root_id = data.get("rootId", "entity [BFO:0000001]")
    import_intermediates = data.get("intermediates", "all")
    import_prefix = data.get("prefix", None)
    import_terms = data.get("terms", [])

    ontology_import = OntologyImport(
        id=import_ontology_id,
        iri=import_purl,
        root_id=import_root_id,
        imported_terms=[TermIdentifier(**t) for t in import_terms],
        intermediates=import_intermediates,
        prefixes=[tuple(x.split(":")) for x in import_prefix] if import_prefix is not None else []
    )

    if update_imports(repo, repository.full_name, gh, [ontology_import], repository.main_branch):
        return Response(status=201)
    else:
        return Response(status=200)


def update_imports(repo: str, repository: str, gh: GitHub, imps: List[OntologyImport], branch: str):
    external_file = None
    if repo == "BCIO":
        external_file = "Upper Level BCIO/inputs/BCIO_External_Imports.xlsx"
    elif repo == "GMHO":
        external_file = "UpperLevel/GMHO_External_Imports.xlsx"
    elif repo == "AddictO":
        external_file = "imports/External_Imports.xlsx"

    if external_file is not None:
        spreadsheet_file = gh.get(f'repos/{repository}/contents/{external_file}')
        base64_bytes = spreadsheet_file['content'].encode('utf-8')
        decoded_data = base64.decodebytes(base64_bytes)
        wb = openpyxl.load_workbook(io.BytesIO(decoded_data))
        sheet: Worksheet = wb.active

        data = sheet.rows
        header = next(data)
        by_id = dict((i.id.lower(), i) for i in imps)

        id_c = next((i for i, h in enumerate(header) if h.value == "IDs"))
        found = []
        for row in data:
            imp = by_id.get(row[0].value.lower(), None)
            if imp is not None:
                found.append(imp.id.lower())
                current = row[id_c].value
                if current is None:
                    ids = set()
                else:
                    ids = {i.strip() for i in current.split(";")}

                old_ids = ids
                ids = set().union(ids, {f"{i.label} [{i.id}]" for i in imp.imported_terms})

                if old_ids == ids:
                    continue

                row[id_c].value = "; ".join(ids)

        # for id, imp in by_id.items():
        #     if id not in found:
        #         ids_str = '; '.join([f"{i.label} [{i.id}]" for i in imp.imported_terms])
        #         sheet.append([imp.id,
        #                       imp.iri,
        #                       imp.root_id if isinstance(imp.root_id,
        #                                                 str) else f"{imp.root_id.label} [{imp.root_id.id}]",
        #                       ids_str,
        #                       imp.intermediates,
        #                       ";".join(f"{p}: {i}" for p, i in imp.prefixes)])

        spreadsheet_stream = io.BytesIO()
        wb.save(spreadsheet_stream)
        github.save_file(gh, repository, external_file, spreadsheet_stream.getvalue(),
                         "Imported IDs", branch)

        return True
