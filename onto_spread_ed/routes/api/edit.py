import base64
import io
import json
import os

import jsonschema
import openpyxl
from flask import Blueprint, request, jsonify, current_app, g, Response
from flask_github import GitHub, GitHubError
from openpyxl.worksheet.worksheet import Worksheet

from onto_spread_ed.PermissionManager import PermissionManager
from onto_spread_ed.SpreadsheetSearcher import SpreadsheetSearcher
from onto_spread_ed.guards.with_permission import requires_permissions
from onto_spread_ed.model.ExcelOntology import ExcelOntology
from onto_spread_ed.model.ReleaseScript import ReleaseScript
from onto_spread_ed.services.ConfigurationService import ConfigurationService
from onto_spread_ed.services.FileCache import FileCache
from onto_spread_ed.utils import github, get_spreadsheet

bp = Blueprint("api_edit", __name__, url_prefix="/api/edit")


@bp.route("/<repo>/<path:path>", methods=["PATCH"])
@requires_permissions("edit")
def edit(repo: str, path: str, gh: GitHub, config: ConfigurationService):
    user_name = g.user.github_login if g.user else "*"
    user_repos = (config.app_config['USERS']
                  .get(user_name, config.app_config['USERS'].get("*", {}))
                  .get("repositories", []))

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

    repository = config.get(repo)

    id = data["id"]
    term_id = data["term"].get("id", None)
    term_label = data["term"].get("label", None)
    term_parent = data["term"].get("parent", None)

    spreadsheet_file = gh.get(f'repos/{repository.full_name}/contents/{path}')
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
        if row[0].value.lower() == id.lower():
            found = True
            if term_id is not None:
                row[0].value = term_id
                changed += [("id", term_id)]

            if term_parent is not None:
                row[parent_col].value = term_parent
                changed += [("parent", term_parent)]

            if term_label is not None:
                row[label_col].value = term_label
                changed = [("label", term_label)]

    if not found:
        return jsonify({"msg": f"No such term with id '{id}'"}), 404

    if len(changed) > 0:
        branch = repository.main_branch

        spreadsheet_stream = io.BytesIO()
        wb.save(spreadsheet_stream)
        msg = f"Updating {path.split('/')[-1]}\n\n" + "\n".join([f"Set {f} to '{v}' for {id}" for f, v in changed])
        github.save_file(gh, repository.full_name, path, spreadsheet_stream.getvalue(), msg, branch)

        return Response(status=200)

    return Response(status=204)


@bp.route("/get/<repo>/<path:path>", methods=["GET"])
@requires_permissions("view")
def get_data(repo: str, path: str, gh: GitHub, config: ConfigurationService, permission_manager: PermissionManager,
             searcher: SpreadsheetSearcher):
    if not permission_manager.current_user_has_permissions(repository=repo):
        return jsonify({"success": False, "error": f"No such repository '{repo}'"}), 404

    [folder, spreadsheet] = path.rsplit('/', 1)

    repository = config.get(repo)
    try:
        (file_sha, rows, header) = get_spreadsheet(gh, repository.full_name, folder, spreadsheet)

        suggestions = [f['label'] for f in searcher.search_for(repo, "label:(?*)", limit=None) if "label" in f]

        data = dict(
            header=header,
            rows=rows,
            file_sha=file_sha,
            repo_name=repo,
            folder=path,
            spreadsheet_name=spreadsheet,
        )

        return jsonify({"success": True, "spreadsheet": data, "suggestions": suggestions}), 200
    except GitHubError as e:
        current_app.logger.error(e)
        return jsonify({"success": False, "error": f"Failed when communicating with github: {e}"}), 200


@bp.route("/suggestions/<repo>", methods=["GET"])
@requires_permissions("view")
def get_suggestions(repo: str, permission_manager: PermissionManager, config: ConfigurationService, gh: GitHub,
                    searcher: SpreadsheetSearcher, cache: FileCache):
    if not permission_manager.current_user_has_permissions(repository=repo):
        return jsonify({"success": False, "error": f"No such repository '{repo}'"}), 404

    suggestions_index = [f['label'] for f in searcher.search_for(repo, "label:(?*)", limit=None) if "label" in f]

    repo = config.get(repo)
    release_script = ReleaseScript.from_json(json.loads(config.get_file(repo, repo.release_script_path)))

    suggestions_external = []
    try:
        external_raw = cache.get_from_github(gh, repo.full_name, release_script.external.target.file).decode()

        external = ExcelOntology.from_owl(external_raw, repo.prefixes).value

        suggestions_external = [t.label for t in external.terms()]
    except Exception as e:
        current_app.logger.error(e)

    suggestions = suggestions_index + suggestions_external

    return jsonify({"success": True, "suggestions": suggestions}), 200
