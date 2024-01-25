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


# validation checks here:

# recursive check each cell in rowData:


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
