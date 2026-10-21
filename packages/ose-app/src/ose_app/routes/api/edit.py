import base64
import io
import json
import os

import jsonschema
import openpyxl
from flask import Blueprint, request, jsonify, current_app, Response
from flask_github import GitHub, GitHubError
from openpyxl.worksheet.worksheet import Worksheet

from ose_app import helpers
from ose_app.PermissionManager import PermissionManager
from ose_app.save import save_from_request
from ose_app.SpreadsheetSearcher import SpreadsheetSearcher
from ose_app.guards.with_permission import requires_permissions
from ose.ontology import ExcelOntology
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.services.FileCache import FileCache
from ose_app.utils import get_spreadsheet, save_file

bp = Blueprint("api_edit", __name__, url_prefix="/api/edit")


@bp.route("/save", methods=["POST"])
@requires_permissions("edit")
def save(searcher: SpreadsheetSearcher, gh: GitHub, config: ConfigurationService,
         permission_manager: PermissionManager):
    d = helpers.json_object()
    if d is None:
        return jsonify(helpers.NOT_AN_OBJECT), 400
    repo_key = d.get("repo_key")
    if repo_key not in helpers.visible_repositories(config, permission_manager):
        return jsonify({"success": False, "error": f"No such repository '{repo_key}'"}), 404

    return save_from_request(searcher, gh, config, d)


@bp.route("/check-updates", methods=["POST"])
@requires_permissions("view")
def check_updates(gh: GitHub, config: ConfigurationService, permission_manager: PermissionManager):
    d = helpers.json_object()
    if d is None:
        return jsonify(helpers.NOT_AN_OBJECT), 400
    repo_key = d.get("repo_key")
    if repo_key not in helpers.visible_repositories(config, permission_manager):
        return jsonify({"success": False, "error": f"No such repository '{repo_key}'"}), 404

    up_to_date = helpers.is_up_to_date(gh, config, d.get("repo_key"), d.get("folder"), d.get("spreadsheet"),
                                       d.get("file_sha"), d.get("branch"))
    return jsonify({"up_to_date": up_to_date})


@bp.route("/<repo>/<path:path>", methods=["PATCH"])
@requires_permissions("edit")
def edit(repo: str, path: str, gh: GitHub, config: ConfigurationService, permission_manager: PermissionManager):
    if not permission_manager.current_user_has_permissions(repository=repo):
        return jsonify({"msg": f"No such repository '{repo}'"}), 404

    static_folder = current_app.static_folder
    assert static_folder is not None

    schema: dict
    with open(os.path.join(static_folder, "schema", "req_body_edit.json"), "r") as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    repository = config.get(repo)
    if repository is None:
        return jsonify({"msg": f"No such repository '{repo}'"}), 404

    id = data["id"]
    term_id = data["term"].get("id", None)
    term_label = data["term"].get("label", None)
    term_parent = data["term"].get("parent", None)

    branch = data.get("branch", repository.main_branch)

    params = {"ref": branch} if branch != repository.main_branch else {}
    spreadsheet_file = gh.get(f'repos/{repository.full_repository_name}/contents/{path}', params=params)
    base64_bytes = spreadsheet_file['content'].encode('utf-8')
    decoded_data = base64.decodebytes(base64_bytes)
    wb = openpyxl.load_workbook(io.BytesIO(decoded_data))
    sheet = wb.active
    if not isinstance(sheet, Worksheet):
        return jsonify({"msg": "File has no active sheet"}), 400

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
        row_id = row[0].value
        if isinstance(row_id, str) and row_id.lower() == id.lower():
            found = True
            if term_id is not None:
                row[0].value = term_id
                changed += [("id", term_id)]

            if term_parent is not None and parent_col is not None:
                row[parent_col].value = term_parent
                changed += [("parent", term_parent)]

            if term_label is not None and label_col is not None:
                row[label_col].value = term_label
                changed = [("label", term_label)]

    if not found:
        return jsonify({"msg": f"No such term with id '{id}'"}), 404

    if len(changed) > 0:
        spreadsheet_stream = io.BytesIO()
        wb.save(spreadsheet_stream)
        msg = f"Updating {path.split('/')[-1]}\n\n" + "\n".join([f"Set {f} to '{v}' for {id}" for f, v in changed])
        save_file(gh, repository.full_repository_name, path, spreadsheet_stream.getvalue(), msg, branch)

        return Response(status=200)

    return Response(status=204)


@bp.route("/get/<repo>/<path:path>", methods=["GET"])
@requires_permissions("view")
def get_data(repo: str, path: str, gh: GitHub, config: ConfigurationService, permission_manager: PermissionManager):
    if not permission_manager.current_user_has_permissions(repository=repo):
        return jsonify({"success": False, "error": f"No such repository '{repo}'"}), 404

    path_parts = reversed(path.rsplit("/", 1))
    spreadsheet = next(path_parts)
    folder = next(path_parts, "")

    repository = config.get(repo)
    if repository is None:
        return jsonify({"success": False, "error": f"No such repository '{repo}'"}), 404

    branch = request.args.get("branch", None)
    try:
        (file_sha, rows, header) = get_spreadsheet(gh, repository.full_repository_name, path, branch=branch)

        data = dict(
            header=header,
            rows=rows,
            file_sha=file_sha,
            repo_name=repo,
            folder=folder,
            spreadsheet_name=spreadsheet,
        )

        return jsonify({"success": True, "spreadsheet": data}), 200
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

    project = config.get(repo)
    if project is None:
        return jsonify({"success": False, "error": f"No such repository '{repo}'"}), 404

    suggestions_external: list[str] = []
    try:
        external_raw = cache.get_from_github(gh, project.full_repository_name, project.external.target.file).decode()

        external = ExcelOntology.from_owl(external_raw, project.prefixes).value_or_raise()

        suggestions_external = [t.label for t in external.terms()]
    except Exception as e:
        current_app.logger.error(e)

    suggestions = suggestions_index + suggestions_external

    return jsonify({"success": True, "suggestions": suggestions}), 200
