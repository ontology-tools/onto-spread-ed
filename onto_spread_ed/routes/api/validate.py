import json
from typing import Any, Dict

import jsonschema
from flask import Blueprint, request, jsonify

from onto_spread_ed.SpreadsheetSearcher import SpreadsheetSearcher
from onto_spread_ed.guards.verify_login import verify_logged_in

bp = Blueprint("api_validate", __name__, url_prefix="/api/validate")

VERIFY_ENTITY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["repository", "spreadsheet", "entity"],
    "properties": {
        "repository": {
            "type": "string",
        },
        "spreadsheet": {
            "type": "string",
        },
        "entity": {
            "type": "object",
        },
        "old_entity": {
            "type": "object",
        }
    },
    "title": "schema"
}


@bp.route("/entity", methods=("POST",))
@verify_logged_in
def validate_entity(searcher: SpreadsheetSearcher):
    data = json.loads(request.data)

    try:
        jsonschema.validate(data, VERIFY_ENTITY_SCHEMA)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    repo_key, spreadsheet, entity, old_entity = data["repository"], data["spreadsheet"], data["entity"], data[
        "old_entity"]

    # repositories = current_app.config['REPOSITORIES']
    # repo_detail = repositories[repo_key]
    # all_files = get_spreadsheets(github, repo_detail, exclude_pattern=r"(imports/.*)|(.*BCIO_External_Imports.xlsx)|(.*BCIO_Upper_Rels.xlsx)")

    valid, errors, warnings = validate_line(entity, old_entity, repo_key, spreadsheet, searcher)

    return jsonify({
        "success": True,
        "valid": valid,
        "errors": errors,
        "warnings": warnings
    })


def validate_line(entity: Dict[str, Any],
                  old_entity: Dict[str, Any],
                  repository: str,
                  file: str,
                  # all_files: list[str],
                  searcher: SpreadsheetSearcher) -> (bool, [Dict[str, Any]]):
    relations: Dict[str, str] = dict(
        (k[k.index("'") + 1:k.rindex("'")], v) for k, v in entity.items() if k.startswith("REL"))

    errors = []
    warnings = []
    # relations_defined = {}
    # parent_defined = False

    parent_result = searcher.search_for(repository, f"label:'{entity['Parent']}'")
    parent_result = [p for p in parent_result if p['label'] == entity['Parent']]
    if not any(parent_result):
        errors.append({
            "type": "unknown-parent",
            "id": entity["ID"],
            "parent": entity["Parent"]
        })

    old_label = old_entity["Label"]
    duplicate_ids = searcher.search_for(repository, f"class_id:'{entity['ID']}'")
    duplicate_ids = [i for i in duplicate_ids if i['class_id'] == entity['ID']]  # Do strict filtering
    if len(duplicate_ids) > 1 or len(duplicate_ids) == 1 and not (
            duplicate_ids[0]["label"] == old_label and duplicate_ids[0]["spreadsheet"] == file):
        errors.append({
            "type": "duplicate-id",
            "id": entity["ID"],
            "labels": [e["label"] for e in duplicate_ids]
        })

    duplicate_labels = searcher.search_for(repository, f"label:'{entity['Label']}'")
    duplicate_labels = [l for l in duplicate_labels if l['label'] == entity['Label']]  # Do strict filtering
    if len(duplicate_labels) > 1 or len(duplicate_labels) == 1 and not (
            duplicate_labels[0]["class_id"] == old_entity["ID"] and duplicate_labels[0]["spreadsheet"] == file):
        errors.append({
            "type": "duplicate-label",
            "ids": [e["label"] for e in duplicate_labels],
            "label": entity["Label"]
        })

    if old_entity["ID"] != entity["ID"]:
        warnings.append({
            "type": "id-changed"
        })

    if old_label != entity["Label"]:
        references = searcher.search_for(repository, f"parent:'{old_label}'")
        references = [r for r in references if r['parent'] == old_label]   # Do strict filtering
        warnings += [{
            "type": "dangling-reference",
            "id": r["class_id"],
            "label": r["label"],
            "spreadsheet": r['spreadsheet']
        } for r in references]

    for relation, value in relations.items():
        if value is None or value.strip() == "":
            continue
        related_entities = searcher.search_for(repository, f"label:'{value}'")
        related_entities = [e for e in related_entities if e['label'] == value]
        if len(related_entities) == 0:
            errors.append({
                "type": "unknown-relation-target",
                "relation": relation,
                "relation-target": value
            })

    # relation_search = " OR ".join(f'' for r in relations.keys())
    #
    # for name, value in relations.items():
    #     errors.append({
    #         "type": "unknown-relation",
    #         "id": entity["ID"],
    #         "relation": name,
    #         "value": value
    #     })

    # for f in all_files:
    #     _, rows, header = get_spreadsheet(github, repository, "", f)
    #     excel = [{**r, "ID": r["BCIO_ID"], "Label": r["Name"] } if "BCIO_ID" in r else r for r in rows if r is not None]
    #
    #     current_app.logger.debug(f"Looking at {f}")
    #     ids = [e["ID"] for e in excel]
    #     labels = [e["Label"] for e in excel]
    #
    #     if f != file and entity["ID"] in ids:
    #         errors.append({
    #             "type": "duplicate-id",
    #             "id": entity["ID"],
    #             "labels": [entity["Label"]] + [e["Label"] for e in excel if e["ID"] == entity["ID"]]
    #         })
    #
    #     if not parent_defined and (entity["Parent"] in labels or entity["Parent"] in ids):
    #         parent_defined = True
    #
    #     for name, value in relations.items():
    #         if value.strip() != "" and name not in relations_defined:
    #             relations_defined[name] = False
    #
    #         if value in ids or value in labels:
    #             relations_defined[name] = True
    #
    # if not parent_defined:
    #     errors.append({
    #         "type": "unknown-parent",
    #         "id": entity["ID"],
    #         "parent": entity["Parent"]
    #     })

    # for rel, defined in relations_defined.items():
    #     if not defined:
    #         errors.append({
    #             "type": "unknown-relation",
    #             "id": entity["ID"],
    #             "relation": rel
    #         })

    return not any(errors), errors, warnings


@bp.route("/file", methods=("POST",))
@verify_logged_in
def validate_file():
    pass
