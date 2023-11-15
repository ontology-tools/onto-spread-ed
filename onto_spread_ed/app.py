# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
# [START gae_python37_app]
import io
import json
import threading
import traceback
from datetime import date
from datetime import datetime

import daff
import openpyxl
from flask import request, g, session, redirect, url_for, render_template
from openpyxl.styles import Font
from openpyxl.styles import PatternFill

from config import *
from database.User import User
from guards.admin import verify_admin
from guards.verify_login import verify_logged_in
from onto_spread_ed.utils.github import get_csv, get_spreadsheet

# setup sqlalchemy

logger = logging.getLogger(__name__)

# app = FlaskApp(__name__)

# cache.set("latestID",0) #initialise caching

# app.config["github"] = github
# searcher = SpreadsheetSearcher(cache, app.config, github)
# app.config["searcher"] = searcher






# Pages for the app
@app.route("/rebuild-index")
@verify_admin
def rebuild_index():
    sheets = searcher.rebuild_index()
    return ('<h1>Index rebuild</h1>'
            '<p>The index was rebuild successfully</p>'
            '<p><a href="/">Go back to main page</a></p>'
            '<h3> Files included in the index</h3>'
            '<ul>'
            f"{''.join(f'<li>{s}</li>' for s in sheets)}"
            '</ul>')





@app.route("/validate", methods=["POST"])
@verify_logged_in
def verify():
    if request.method == "POST":
        cell = json.loads(request.form.get("cell"))
        column = json.loads(request.form.get("column"))
        rowData = json.loads(request.form.get("rowData"))
        headers = json.loads(request.form.get("headers"))
        table = json.loads(request.form.get("table"))
        # check for blank cells under conditions first:
    blank = {}
    unique = {}
    returnData, uniqueData = checkBlankMulti(1, blank, unique, cell, column, headers, rowData, table)
    if len(returnData) > 0 or len(uniqueData) > 0:
        return (json.dumps({"message": "fail", "values": returnData, "unique": uniqueData}))
    return ('success')


@app.route("/generate", methods=["POST"])
@verify_logged_in
def generate():
    if request.method == "POST":
        repo_key = request.form.get("repo_key")
        rowData = json.loads(request.form.get("rowData"))
        values = {}
        ids = {}
        for row in rowData:
            nextIdStr = str(searcher.get_next_id(repo_key))
            fill_num = app.config['DIGIT_COUNT']
            if repo_key == "BCIO":
                fill_num = fill_num - 1
            else:
                fill_num = fill_num
            id = repo_key.upper() + ":" + nextIdStr.zfill(fill_num)
            ids["ID" + str(row['id'])] = str(row['id'])
            values["ID" + str(row['id'])] = id
        return (json.dumps({"message": "idlist", "IDs": ids, "values": values}))  # need to return an array
    return ('success')


# validation checks here: 

# recursive check each cell in rowData:
def checkBlankMulti(current, blank, unique, cell, column, headers, rowData, table):
    for index, (key, value) in enumerate(
            rowData.items()):  # todo: really, we need to loop here, surely there is a faster way?
        if index == current:
            if key == "Label" or key == "Definition" or key == "Parent" or key == "Sub-ontology" or key == "Curation status":
                if key == "Definition" or key == "Parent":
                    status = rowData.get("Curation status")  # check for "Curation status"
                    if (status):
                        if rowData["Curation status"] == "Proposed" or rowData["Curation status"] == "External":
                            pass
                        else:
                            if value.strip() == "":
                                blank.update({key: value})
                    else:
                        pass  # no "Curation status" column
                else:
                    if value.strip() == "":
                        blank.update({key: value})
                    else:
                        pass
            if key == "Label" or key == "ID" or key == "Definition":
                if checkNotUnique(value, key, headers, table):
                    unique.update({key: value})
    # go again:
    current = current + 1
    if current >= len(rowData):
        return (blank, unique)
    return checkBlankMulti(current, blank, unique, cell, column, headers, rowData, table)


def checkNotUnique(cell, column, headers, table):
    counter = 0
    cellStr = cell.strip()
    if cellStr == "":
        return False
    # if Label, ID or Definition column, check cell against all other cells in the same column and return true if same
    for r in range(len(table)):
        row = [v for v in table[r].values()]
        del row[0]  # remove extra numbered "id" column
        for c in range(len(headers)):
            if headers[c] == "ID" and column == "ID":
                if row[c].strip() == cellStr:
                    counter += 1
                    if counter > 1:  # more than one of the same
                        return True
            if headers[c] == "Label" and column == "Label":
                if row[c].strip() == cellStr:
                    counter += 1
                    if counter > 1:
                        return True
            if headers[c] == "Definition" and column == "Definition":
                if row[c].strip() == cellStr:
                    counter += 1
                    if counter > 1:
                        return True
    return False




# api:


# TODO: NEVER USED?
@app.route('/visualise/<repo>/<sheet>')
@verify_logged_in  # todo: does this need to be disabled to allow cross origin requests? apparently not!
def visualise(repo, sheet):
    # print("reached visualise")
    return render_template("templates/visualise.html", sheet=sheet, repo=repo)


# TODO: NEVER USED?
@app.route('/openPat', methods=['POST'])
@verify_logged_in
def openPat():
    if request.method == "POST":
        repo = request.form.get("repo")
        # print("repo is ", repo)
        sheet = request.form.get("sheet")
        # print("sheet is ", sheet)
        table = json.loads(request.form.get("table"))
        # print("table is: ", table)
        indices = json.loads(request.form.get("indices"))
        # print("indices are: ", indices)

        if repo not in ontodb.releases:
            ontodb.parseRelease(repo)
        if len(indices) > 0:  # selection
            # ontodb.parseSheetData(repo,table)
            allIDS = ontodb.getIDsFromSelection(repo, table, indices)
            # print("got allIDS: ", allIDS)
        else:  # whole sheet..
            ontodb.parseSheetData(repo, table)
            allIDS = ontodb.getIDsFromSheet(repo, table)
            # todo: do we need to do above twice?

        # print("allIDS: ", allIDS)
        # remove duplicates from allIDS:
        allIDS = list(dict.fromkeys(allIDS))

        allData = ontodb.getMetaData(repo, allIDS)
        # print("allData: ", allData) 
        # print("dotStr is: ", dotStr)
        return render_template("pat.html", repo=repo, all_ids=allIDS, all_data=allData)  # todo: PAT.html

    return ("Only POST allowed.")


# TODO: NEVER USED
@app.route('/openPatAcrossSheets', methods=['POST'])
@verify_logged_in
def openPatAcrossSheets():
    # build data we need for dotStr query (new one!)
    if request.method == "POST":
        idString = request.form.get("idList")
        # print("idString is: ", idString)
        repo = request.form.get("repo")
        logger.debug("repo is %s", repo)
        idList = idString.split()
        logger.debug("idList: %s", idList)
        # for i in idList:
        #     print("i is: ", i)
        # indices = json.loads(request.form.get("indices"))
        # print("indices are: ", indices)
        ontodb.parseRelease(repo)
        # todo: do we need to support more than one repo at a time here?
        allIDS = ontodb.getRelatedIDs(repo, idList)
        # print("allIDS: ", allIDS)
        # remove duplicates from allIDS:
        allIDS = list(dict.fromkeys(allIDS))

        # todo: all experimental from here:
        allData = ontodb.getMetaData(repo, allIDS)
        # print("TEST allData: ", allData)

        # dotStr = ontodb.getDotForIDs(repo,idList).to_string()
        return render_template("pat.html", repo=repo, all_ids=allIDS, all_data=allData)  # todo: PAT.html

    return ("Only POST allowed.")


# TODO: NEVER USED?
@app.route('/save_new_ontology', methods=['POST'])
@verify_logged_in
def save_new_ontology():
    new_ontology = request.form.get("new_ontology")
    logger.debug("Received new Ontology: %s" + new_ontology)
    response = "test"
    return (json.dumps({"message": "Success",
                        "response": response}), 200)


# TODO: NEVER USED?
@app.route('/update_ids', methods=['POST'])
@verify_logged_in
def update_ids():
    current_ontology = request.form.get("current_ontology")
    new_IDs = request.form.get("new_IDs")
    logger.debug("Received new IDs from : %s" + current_ontology)
    logger.debug("data is: %s", new_IDs)
    response = "test"
    return (json.dumps({"message": "Success",
                        "response": response}), 200)


# Internal methods







if __name__ == "__main__":  # on running python app.py

    app.run(debug=app.config["DEBUG"], port=8080)  # run the flask app

# [END gae_python37_app]
