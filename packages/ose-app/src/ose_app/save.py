import base64
import io
import json
import threading
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import daff
import openpyxl
from flask import current_app, g, jsonify
from flask_github import GitHub
from openpyxl.styles import Font, PatternFill

from ose_app.SpreadsheetSearcher import SpreadsheetSearcher
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.utils import get_spreadsheet, create_branch


def save_spreadsheet(searcher: SpreadsheetSearcher, github: GitHub, config: ConfigurationService, repo_key: str,
                     path: str, row_data_parsed, initial_data_parsed, file_sha_original: str, commit_msg: str,
                     commit_msg_extra: str, header, merge_strategy: str, target_branch: str = None):
    overwrite = merge_strategy is not None

    id_suffix = ""

    repository = config.get(repo_key)
    default_branch = target_branch or repository.main_branch

    if path in repository.readonly_files:
        return jsonify({
            "success": False,
            "error": f"The file is readonly: {repository.readonly_files[path]}",
        }), 405

    try:
        if merge_strategy == "theirs":
            (sha, rows, header) = get_spreadsheet(github, repository.full_repository_name, path, branch=default_branch)
            return jsonify({
                "success": True,
                "new_rows": rows,
                "new_header": header,
                "new_sha": sha,
                "merge_strategy": merge_strategy
            })

        # Sort based on label
        # What if 'Label' column not present?
        if 'Label' in header:
            row_data_parsed = sorted(row_data_parsed, key=lambda k: k['Label'] if k['Label'] else "")
        elif 'Relationship' in header:
            row_data_parsed = sorted(row_data_parsed, key=lambda k: k['Relationship'] if k['Relationship'] else "")

            id_suffix = "R"  # For relations add a 'R' as a suffix
        else:
            current_app.logger.warning(
                "While saving: No Label column present, so not sorting this.")  # do we need to sort - yes, for diff!

        current_app.logger.debug(f"Got file_sha: {file_sha_original}")

        next_id = searcher.get_next_id(repo_key + id_suffix)

        wb = openpyxl.Workbook()
        sheet = wb.active

        for c in range(len(header)):
            sheet.cell(row=1, column=c + 1).value = header[c]
            sheet.cell(row=1, column=c + 1).font = Font(size=12, bold=True)
        for r, row in enumerate(row_data_parsed):
            if "id" in row:
                del row["id"]  # Tabulator-added ID column
            for c, field in enumerate(header):
                sheet.cell(row=r + 2, column=c + 1).value = row[field]
                # Set row background colours according to 'Curation status'
                # These should be kept in sync with those used in edit screen
                # TODO add to config
                # What if "Curation status" not present?
                if 'Curation status' in header:
                    if row["Curation status"] == "Discussed":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="ffe4b5", fill_type="solid")
                    elif row["Curation status"] == "Ready":  # this is depreciated
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="98fb98", fill_type="solid")
                    elif row["Curation status"] == "Proposed":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="ffffff", fill_type="solid")
                    elif row["Curation status"] == "Pre-proposed":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="ebfad0", fill_type="solid")
                    elif row["Curation status"] == "To Be Discussed":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="eee8aa", fill_type="solid")
                    elif row["Curation status"] == "In Discussion":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="fffacd", fill_type="solid")
                    elif row["Curation status"] == "Published":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="7fffd4", fill_type="solid")
                    elif row["Curation status"] == "Obsolete":
                        sheet.cell(row=r + 2, column=c + 1).fill = PatternFill(fgColor="2f4f4f", fill_type="solid")

            # Generate identifiers:
            if 'ID' in header:
                if not row["ID"]:  # blank
                    label, parent, definition = None, None, None
                    if {'Label', 'Parent', 'Definition'} <= set(header):  # make sure we have the right sheet
                        label = row["Label"]
                        parent = row["Parent"]
                        definition = row["Definition"]
                    elif {'Relationship', 'Parent relationship', 'Definition'} <= set(header):
                        label = row["Relationship"]
                        parent = row["Parent relationship"]
                        definition = row["Definition"]

                    curation_status: str = row.get("Curation status", "None")
                    if curation_status.lower().strip() != "pre-proposed" and \
                            label and (parent or 'Relationship' in header) and definition:
                        # generate ID here:
                        nextIdStr = str(next_id)
                        next_id += 1
                        fill_num = repository.id_digits
                        if repo_key == "BCIO":
                            fill_num = fill_num - 1
                        else:
                            fill_num = fill_num
                        id = repo_key.upper() + id_suffix + ":" + nextIdStr.zfill(fill_num)
                        new_id = id
                        row_data_parsed[r]["ID"] = new_id
                        for c in range(len(header)):
                            if c == 0:
                                sheet.cell(row=r + 2, column=c + 1).value = new_id

        # Create version for saving
        spreadsheet_stream = io.BytesIO()
        wb.save(spreadsheet_stream)

        # base64_bytes = base64.b64encode(sample_string_bytes)
        base64_bytes = base64.b64encode(spreadsheet_stream.getvalue())
        base64_string = base64_bytes.decode("ascii")

        # Create a new branch to commit the change to (in case of simultaneous updates)
        branch = f"{g.user.github_login}_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')}"
        create_branch(github, repository.full_repository_name, branch, default_branch)

        current_app.logger.debug("About to get latest version of the spreadsheet file %s",
                                 f"repos/{repository.full_repository_name}/contents/{path}")
        # Get the sha for the file
        (file_sha_theirs, new_rows, new_header) = get_spreadsheet(github, repository.full_repository_name, path,
                                                                  branch=default_branch)

        # Commit changes to branch (replace code with sheet)
        data = {"message": commit_msg, "content": base64_string, "branch": branch, "sha": file_sha_theirs}
        current_app.logger.debug("About to commit file to branch %s",
                                 f"repos/{repository.full_repository_name}/contents/{path}")
        response = github.put(f"repos/{repository.full_repository_name}/contents/{path}", data=data)
        if not response:
            raise Exception(
                f"Unable to commit addition of {path} to branch {branch} in {repository.full_repository_name}"
            )

        # Create a PR for the change
        current_app.logger.debug("About to create PR from branch", )
        response = github.post(
            f"repos/{repository.full_repository_name}/pulls",
            data={
                "title": commit_msg,
                "head": branch,
                "base": default_branch,
                "body": commit_msg_extra
            },
        )
        if not response:
            raise Exception(f"Unable to create PR for branch {branch} in {repository.full_repository_name}")
        pr_info = response['html_url']

        # Do not merge automatically if this file was stale as that will overwrite the other changes

        if file_sha_theirs != file_sha_original and not overwrite:
            current_app.logger.info("PR created and must be merged manually as repo file had changed")

            # Get the changes between the new file and this one:
            conflicts, merged_data = get_diff(initial_data_parsed, row_data_parsed, new_rows, new_header)

            if len(conflicts) > 0:

                # Delete the branch again
                current_app.logger.debug("About to delete branch",
                                         f"repos/{repository.full_repository_name}/git/refs/heads/{branch}")
                response = github.delete(
                    f"repos/{repository.full_repository_name}/git/refs/heads/{branch}")
                if not response:
                    raise Exception(f"Unable to delete branch {branch} in {repository.full_repository_name}")

                return jsonify({
                    "success": False,
                    "error": "merge-conflict",
                    "pr": pr_info,
                    "file_sha_1": file_sha_original,
                    "file_sha_2": file_sha_theirs,
                    "merge_conflicts": [{
                        "row": c.row - 1,  # subtract 1 for header row which we excluded
                        "col": new_header[c.col],
                        "base_value": c.pvalue,
                        "our_value": c.lvalue,
                        "their_value": c.rvalue
                    } for c in conflicts],
                    "merged_table": merged_data,
                })
            else:
                return save_spreadsheet(searcher, github, config, repo_key, path, merged_data, initial_data_parsed,
                             file_sha_original, commit_msg, commit_msg_extra, header, "automatic",
                             target_branch=target_branch)

            # return (
            #     json.dumps({
            #         'Error': 'Your change was submitted to the repository but could not be automatically merged due '
            #                  'to a conflict. You can view the change <a href="'
            #                  + pr_info + '" target = "_blank" >here </a>. ', "file_sha_1": file_sha_original,
            #         "file_sha_2": file_sha_theirs, "pr_branch": branch, "merge_diff": merge_diff,
            #         "merged_table": json.dumps(merged_table),
            #         "rows3": rows3, "header3": header3}), 300  # 400 for missing REPO
            # )
        else:
            # Merge the created PR
            current_app.logger.debug("About to merge created PR")
            response = github.post(
                f"repos/{repository.full_repository_name}/merges",
                data={
                    "head": branch,
                    "base": default_branch,
                    "commit_message": commit_msg
                },
            )
            if not response:
                raise Exception(f"Unable to merge PR from branch {branch} in {repository.full_repository_name}")

            # Delete the branch again
            current_app.logger.debug("About to delete branch %s",
                                     f"repos/{repository.full_repository_name}/git/refs/heads/{branch}")
            response = github.delete(
                f"repos/{repository.full_repository_name}/git/refs/heads/{branch}")
            if not response:
                raise Exception(f"Unable to delete branch {branch} in {repository.full_repository_name}")

        current_app.logger.info("Save succeeded.")
        # Update the search index for this file ASYNCHRONOUSLY (don't wait)
        thread = threading.Thread(target=searcher.update_index,
                                  args=(repo_key, path, row_data_parsed))
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

        # Get the sha AGAIN for the file
        (saved_sha, saved_rows, saved_header) = get_spreadsheet(github, repository.full_repository_name, path,
                                                              branch=default_branch)
        github.get(f"repos/{repository.full_repository_name}/contents/{path}")
        return jsonify({
            "success": True,
            "new_rows": saved_rows,
            "new_header": new_header,
            "new_sha": saved_sha,
            "merge_strategy": merge_strategy
        })

    except Exception as err:
        current_app.logger.error(err)
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(err),
        }), 400


def get_diff(data_base: List[Dict[str, Any]],
             data_ours: List[Dict[str, Any]],
             data_theirs: List[Dict[str, Any]],
             row_header: List[str]) -> Tuple[List[daff.ConflictInfo], List[Dict[str, Any]]]:
    # Normalise rows: drop Tabulator's "id" column and treat "" as None, so all three tables compare equal
    new_data_ours = []
    for k in data_ours:
        dictT = {}
        for key, val, item in zip(k, k.values(), k.items()):
            if key != "id":
                if val == "":
                    val = None
                dictT[key] = val
        new_data_ours.append(dictT)

    new_data_base = []
    for k in data_base:
        dictT2 = {}
        for key, val, item in zip(k, k.values(), k.items()):
            if key != "id":
                if val == "":
                    val = None
                dictT2[key] = val
        new_data_base.append(dictT2)

    new_data_theirs = []
    for h in data_theirs:
        dictT3 = {}
        for key, val, item in zip(h, h.values(), h.items()):
            if key != "id":
                if val == "":
                    val = None
                dictT3[key] = val
        new_data_theirs.append(dictT3)

    row_data_combo_ours = [row_header] + [[r[k] for k in row_header] for r in new_data_ours]
    row_data_combo_base = [row_header] + [[r[k] for k in row_header] for r in new_data_base]
    row_data_combo_theirs = [row_header] + [[r[k] for k in row_header] for r in new_data_theirs]

    daff.Table()

    table_ours = daff.PythonTableView(row_data_combo_ours)  # daff needs a header in order to work correctly!
    table_base = daff.PythonTableView(row_data_combo_base)
    table_theirs = daff.PythonTableView(row_data_combo_theirs)

    merger = daff.Merger(table_base, table_ours, table_theirs, daff.CompareFlags())
    merger.apply()

    merged_data = [{h: row[i] for (i, h) in enumerate(row_header)} for row in table_ours.data[1:]]

    return merger.getConflictInfos(), merged_data


def _bad_request(message: str):
    return jsonify({"success": False, "error": message}), 400


def _parse_json_field(save_data: dict, name: str, required: bool):
    value = save_data.get(name)
    if value is None or value == "":
        if required:
            return None, f"Missing field '{name}'"
        return [], None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as e:
            return None, f"Field '{name}' is not valid JSON: {e}"
    if not isinstance(value, list) or not all(isinstance(r, dict) for r in value):
        return None, f"Field '{name}' must be a list of row objects"
    return value, None


def save_from_request(searcher: SpreadsheetSearcher, github: GitHub, config: ConfigurationService, save_data: dict):
    """Handles a save request body (`/api/edit/save`). Invalid requests answer 400 `{success: false, error}`."""
    if not isinstance(save_data, dict):
        return _bad_request("Request body must be a JSON object")

    for name in ("repo_key", "path", "file_sha"):
        if not isinstance(save_data.get(name), str) or not save_data[name].strip():
            return _bad_request(f"Missing or invalid field '{name}'")

    header = save_data.get("header")
    if not isinstance(header, list) or not all(isinstance(h, str) for h in header):
        return _bad_request("Missing or invalid field 'header' (must be a list of column names)")

    row_data, error = _parse_json_field(save_data, "rowData", required=True)
    if error:
        return _bad_request(error)
    initial_data_parsed, error = _parse_json_field(save_data, "initialData", required=False)
    if error:
        return _bad_request(error)

    # Sort based on label
    # What if 'Label' column not present?
    initial_data = sorted(initial_data_parsed, key=lambda k: k.get('Label', None) or "")

    return save_spreadsheet(searcher, github, config, save_data["repo_key"], save_data["path"], row_data,
                            initial_data, save_data["file_sha"].strip(), save_data.get("commit_msg"),
                            save_data.get("commit_msg_extra"), header,
                            save_data.get("merge_strategy", None), target_branch=save_data.get("branch", None))
