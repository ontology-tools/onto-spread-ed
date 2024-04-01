import base64
import io
import json
import os

import jsonschema
import openpyxl
from flask import Blueprint, request, jsonify, current_app, g, Response
from flask_github import GitHub
from openpyxl.worksheet.worksheet import Worksheet

from onto_spread_ed.guards.admin import verify_admin
from onto_spread_ed.utils import github

bp = Blueprint("api_edit", __name__, url_prefix="/api/edit")


@bp.route("/<repo>/<path:path>", methods=["PATCH"])
@verify_admin
def edit(repo: str, path: str, gh: GitHub):
    user_repos = current_app.config['USERS_METADATA'][g.user.github_login]["repositories"]

    if repo not in user_repos:
        return jsonify({"msg": f"No such repository '{repo}'"}), 404

    schema: dict
    with open(os.path.join(current_app.static_folder, "schema", "req_body_edit.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    repository = current_app.config['REPOSITORIES'][repo]

    term_id = data["term"]["id"]
    term_label = data["term"].get("label", None)
    term_parent = data["term"].get("parent", None)

    spreadsheet_file = gh.get(f'repos/{repository}/contents/{path}')
    base64_bytes = spreadsheet_file['content'].encode('utf-8')
    decoded_data = base64.decodebytes(base64_bytes)
    wb = openpyxl.load_workbook(io.BytesIO(decoded_data))
    sheet: Worksheet = wb.active

    data = sheet.rows
    header = list(next(data))

    parent_col = next((i for i, h in enumerate(header) if h.value in ["Parent", "Parent class/ BFO class"]), None)
    if parent_col is None and term_parent is not None:
        return jsonify({"msg": "File has no parent column"}), 400

    label_col = next(
        (i for i, h in enumerate(header) if h.value in ["Name", "Label", "Label (synonym)", "Relationship"]), None)
    if label_col is None and term_label is not None:
        return jsonify({"msg": "File has no label column"}), 400

    found = False
    changed = []
    for row in data:
        if row[0].value.lower() == term_id.lower():
            found = True
            if term_parent is not None:
                row[parent_col].value = term_parent
                changed += [("parent", term_parent)]

            if term_label is not None:
                row[label_col].value = term_label
                changed = [("label", term_label)]

    if not found:
        return jsonify({"msg": f"No such term with id '{term_id}'"}), 404

    if len(changed) > 0:
        branch = current_app.config["DEFAULT_BRANCH"][repo]

        spreadsheet_stream = io.BytesIO()
        wb.save(spreadsheet_stream)
        msg = f"Updating {path.split('/')[-1]}\n\n" + "\n".join([f"Set {f} to '{v}' for {term_id}" for f, v in changed])
        github.save_file(gh, repository, path, spreadsheet_stream.getvalue(), msg, branch)

        return Response(status=200)

    return Response(status=204)
