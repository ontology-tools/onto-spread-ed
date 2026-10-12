import json
from graphlib import TopologicalSorter
from io import BytesIO
from typing import Any, Dict, List, Optional

import jsonschema
from flask import Blueprint, request, jsonify, current_app
from flask_github import GitHub
from openpyxl.workbook import Workbook

from ose_app.SpreadsheetSearcher import SpreadsheetSearcher
from ose_app.guards.with_permission import requires_permissions
from ose.ontology import ExcelOntology
from ose.project import ProjectFile
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.services.FileCache import FileCache
from ose_app.utils import get_file

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
                  searcher: SpreadsheetSearcher) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]]]:
    relations: Dict[str, str] = dict(
        (k[k.index("'") + 1:k.rindex("'")], v) for k, v in entity.items() if k.startswith("REL"))

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
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


def order_dependencies(files: Dict[str, ProjectFile]) -> List[tuple[str, ProjectFile]]:
    order = TopologicalSorter({k: f.needs for k, f in files.items()}).static_order()
    return [(k, files[k]) for k in order if not all(s.type == "owl" for s in files[k].sources)]


@bp.route("/file", methods=("POST",))
@requires_permissions("view")
def validate_file(config: ConfigurationService, gh: GitHub, cache: FileCache):
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
    assert ws is not None

    ws.append(header)
    for row in rows:
        ws.append([row[h] for h in header])

    spreadsheet = BytesIO()
    wb.save(spreadsheet)

    project = config.get(repo)
    if project is None:
        return jsonify({"success": False, "error": f"No such repository '{repo}'."}), 404

    o = ExcelOntology(f"temp://{file}")

    if "include-external" in project.validation or "include-dependencies" in project.validation:
        if "include-external" in project.validation:
            try:
                external_raw = cache.get_from_github(
                    gh, project.full_repository_name, project.external.target.file
                ).decode()

                external = ExcelOntology.from_owl(external_raw, project.prefixes).value_or_raise()
                o.import_other_excel_ontology(external)
            except Exception as e:
                current_app.logger.error(e)

        if "include-dependencies" in project.validation:
            file_key: Optional[str]
            file_release_file: Optional[ProjectFile]
            file_key, file_release_file = next(
                ((k, f) for (k, f) in project.files.items() if any(s.file == file for s in f.sources)),
                (None, None))
            if file_key is not None and file_release_file is not None:
                release_files: List[ProjectFile] = [file_release_file]
                needs: List[str] = []
                while len(release_files) > 0:
                    release_file = release_files.pop(0)
                    needs.extend(release_file.needs)
                    release_files.extend([project.files[n] for n in release_file.needs])

                dependencies = order_dependencies(dict((k, project.files[k]) for k in needs))

                other_sources = ExcelOntology("tmp:///other_sources/")

                for source in file_release_file.sources:
                    # Evaluate lazily to avoid loading unnecessary files in case type not in ["classes", "relations"]
                    def excel_source():
                        return spreadsheet if source.file == file else BytesIO(
                            get_file(gh, project.full_repository_name, source.file))

                    ontology = o if source.file == file else other_sources
                    schema = project.spreadsheet_schema(source.spreadsheet_schema)
                    if source.type == "classes":
                        ontology.add_terms_from_excel(source.file, excel_source(), schema)
                    elif source.type == "relations":
                        ontology.add_relations_from_excel(source.file, excel_source(), schema)

                o.import_other_excel_ontology(other_sources)

                for k, dependency in dependencies:
                    dependency_ontology = ExcelOntology(f"tmp:///{k}")
                    for s in dependency.sources:
                        dependency_file = BytesIO(get_file(gh, project.full_repository_name, s.file))
                        dependency_schema = project.spreadsheet_schema(s.spreadsheet_schema)
                        if s.type == "classes":
                            dependency_ontology.add_terms_from_excel(s.file, dependency_file, dependency_schema)
                        elif s.type == "relations":
                            dependency_ontology.add_relations_from_excel(s.file, dependency_file, dependency_schema)

                    o.import_other_excel_ontology(dependency_ontology)
    else:
        o.add_terms_from_excel(file, spreadsheet)

    o.resolve()
    # Exclude missing ID here as they are generated if needed on save
    result = o.validate(exclude=["missing-id"])

    return jsonify({
        "success": True,
        "valid": result.successful,
        "errors": result.log.errors,
        "warnings": result.log.warnings,
        "infos": result.log.infos,
    })
