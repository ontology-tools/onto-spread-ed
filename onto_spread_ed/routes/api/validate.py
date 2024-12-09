import json
import os.path
from email.policy import default
from email.quoprimime import header_check
from io import BytesIO
from json import JSONEncoder
from mailbox import ExternalClashError
from typing import Any, Dict

import jsonschema
from flask import Blueprint, request, jsonify, current_app
from flask_injector import wrap_class_based_view
from openpyxl.workbook import Workbook

from onto_spread_ed.SpreadsheetSearcher import SpreadsheetSearcher
from onto_spread_ed.guards.with_permission import requires_permissions
from onto_spread_ed.model.ExcelOntology import ExcelOntology
from onto_spread_ed.services.ConfigurationService import ConfigurationService

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

VERIFY_FILE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["repository", "spreadsheet", "rows"],
    "properties": {
        "repository": {
            "type": "string",
        },
        "spreadsheet": {
            "type": "string",
        },
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
            }
        }
    }
}


@bp.route("/entity", methods=("POST",))
@requires_permissions("view")
def validate_entity(searcher: SpreadsheetSearcher):
    data = json.loads(request.data)

    try:
        jsonschema.validate(data, VERIFY_ENTITY_SCHEMA)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    repo_key, spreadsheet, entity, old_entity = data["repository"], data["spreadsheet"], data["entity"], data[
        "old_entity"]

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
    duplicate_labels = [label for label in duplicate_labels if label['label'] == entity['Label']]  # Do strict filtering
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
        references = [r for r in references if r['parent'] == old_label]  # Do strict filtering
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

    return not any(errors), errors, warnings


@bp.route("/file", methods=("POST",))
@requires_permissions("view")
def validate_file(config: ConfigurationService):
    data = json.loads(request.data)

    try:
        jsonschema.validate(data, VERIFY_FILE_SCHEMA)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    repo, file, rows = data["repository"], data["spreadsheet"], data["rows"]
    
    if len(rows) < 1:
        return jsonify({
            "success": True,
            "valid": True,
            "errors": [],
            "warnings": [],
            "infos": []
        })
    
    header = list(rows[0].keys())
    
    
    wb = Workbook()
    ws = wb.active
    
    ws.append(header)
    for row in rows:
        ws.append([row[h] for h in header])
        
    spreadsheet = BytesIO()
    wb.save(spreadsheet)
    
    repo = config.get(repo)

    external = ExcelOntology.from_owl(os.path.join(current_app.static_folder, "bcio_external.owl"), repo.prefixes)
    
    o = ExcelOntology(f"temp://{file}")
    o.import_other_excel_ontology(external.value)
    o.add_terms_from_excel(file, spreadsheet)
    o.resolve()
    result = o.validate()
    
    return jsonify({
        "success": True,
        "valid": result.ok() and not result.has_errors(),
        "errors": result.errors,
        "warnings": result.warnings,
        "infos": result.infos,
    })
    
    
