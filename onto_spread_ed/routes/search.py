import json

from flask import Blueprint, request, current_app

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..guards.verify_login import verify_logged_in

bp = Blueprint("search", __name__, template_folder="../templates")


@bp.route('/search', methods=['POST'])
@verify_logged_in
def search(searcher: SpreadsheetSearcher):
    searchTerm = request.form.get("inputText")
    repoName = request.form.get("repoName")
    searchResults = searchAcrossSheets(searcher, repoName, searchTerm)
    searchResultsTable = json.dumps(searchResults)
    return (json.dumps({"message": "Success",
                        "searchResults": searchResultsTable}), 200)


@bp.route('/searchAssignedToMe', methods=['POST'])
@verify_logged_in
def searchAssignedToMe(searcher: SpreadsheetSearcher):
    initials = request.form.get("initials")
    current_app.logger.debug("Searching for initials: " + initials)
    repoName = request.form.get("repoName")
    # below is searching in "Label" column?
    searchResults = searchAssignedTo(searcher, repoName, initials)
    searchResultsTable = json.dumps(searchResults)
    return (json.dumps({"message": "Success",
                        "searchResults": searchResultsTable}), 200)


def searchAcrossSheets(searcher: SpreadsheetSearcher, repo_name, search_string):
    searcherAllResults = searcher.search_for(repo_name, search_string=search_string)
    return searcherAllResults


def searchAssignedTo(searcher: SpreadsheetSearcher, repo_name, initials):
    searcherAllResults = searcher.search_for(repo_name, assigned_user=initials)
    return searcherAllResults