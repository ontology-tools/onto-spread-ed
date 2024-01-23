import json

from flask import Blueprint, request, current_app, render_template

from ..OntologyDataStore import OntologyDataStore
from ..guards.verify_login import verify_logged_in

bp = Blueprint("visualize", __name__, template_folder="../templates")


@bp.route('/api/openVisualiseAcrossSheets', methods=['POST'])
# @verify_logged_in # not enabled for /api/
def apiOpenVisualiseAcrossSheets(ontodb: OntologyDataStore):
    # build data we need for dotStr query (new one!)
    if request.method == "POST":
        idString = request.form.get("idList")
        repo = request.form.get("repo")
        idList = idString.split()
        ontodb.parseRelease(repo)
        dotStr = ontodb.getDotForIDs(repo, idList).to_string()
        # NOTE: APP_TITLE2 can't be blank - messes up the spacing
        APP_TITLE2 = "VISUALISATION"  # could model this on calling url here? Or something else..
        return render_template("visualise.html", sheet="selection", repo=repo, dotStr=dotStr, api=True,
                               APP_TITLE2=APP_TITLE2)


@bp.route('/openVisualise', methods=['POST'])
@verify_logged_in
def openVisualise(ontodb: OntologyDataStore):
    curation_status_filters = ["", "External", "Proposed", "To Be Discussed", "In Discussion", "Discussed", "Published",
                               "Obsolete"]
    dotstr_list = []
    repo = request.form.get("repo")
    sheet = request.form.get("sheet")
    table = json.loads(request.form.get("table"))
    indices = json.loads(request.form.get("indices"))
    try:
        filter = json.loads(request.form.get("filter"))
        if len(filter) > 0:
            pass
        else:
            filter = ""
    except Exception as err:
        filter = ""
        current_app.logger.error(str(err))
    if repo not in ontodb.releases:
        ontodb.parseRelease(repo)

    if len(indices) > 0:  # visualise selection
        # check if filter is greater than 1:
        if len(filter) > 1 and filter != "":  # multi-select:
            for i in range(0, 2):
                ontodb.parseSheetData(repo, table)
                dotStr = ontodb.getDotForSelection(repo, table, indices,
                                                   filter).to_string()  # filter is a list of strings here
        else:
            for filter in curation_status_filters:
                # loop this twice to mitigate ID bug:
                for i in range(0, 2):
                    ontodb.parseSheetData(repo, table)
                    dotStr = ontodb.getDotForSelection(repo, table, indices, filter).to_string()
                # append dotStr to dotstr_list
                dotstr_list.append(dotStr)  # all possible graphs
            # calculate default all values:
            filter = ""  # default
            for i in range(0, 2):
                ontodb.parseSheetData(repo, table)
                dotStr = ontodb.getDotForSelection(repo, table, indices, filter).to_string()

    else:
        # check if filter is greater than 1:
        if len(filter) > 1 and filter != "":  # multi-select:
            for i in range(0, 2):
                ontodb.parseSheetData(repo, table)
                dotStr = ontodb.getDotForSheetGraph(repo, table,
                                                    filter).to_string()  # filter is a list of strings here
                # no dotstr_list here, just one dotStr
                # dotstr_list.append(dotStr) #all possible graphs
        else:
            for filter in curation_status_filters:  # Visualise sheet
                # loop this twice to mitigate ID bug:
                for i in range(0, 2):
                    ontodb.parseSheetData(repo, table)
                    dotStr = ontodb.getDotForSheetGraph(repo, table, filter).to_string()
                # append dotStr to dotstr_list
                dotstr_list.append(dotStr)  # all possible graphs
            # calculate default all values:
            filter = ""  # default
            for i in range(0, 2):
                ontodb.parseSheetData(repo, table)
                dotStr = ontodb.getDotForSheetGraph(repo, table, filter).to_string()

    return render_template("visualise.html", sheet=sheet, repo=repo, dotStr=dotStr, dotstr_list=dotstr_list,
                           filter=filter)

@bp.route('/openVisualiseAcrossSheets', methods=['POST'])
@verify_logged_in
def openVisualiseAcrossSheets(ontodb: OntologyDataStore):
    # build data we need for dotStr query (new one!)
    idString = request.form.get("idList")
    repo = request.form.get("repo")
    idList = idString.split()
    ontodb.parseRelease(repo)
    # todo: do we need to support more than one repo at a time here?
    dotStr = ontodb.getDotForIDs(repo, idList).to_string()
    return render_template("visualise.html", sheet="selection", repo=repo, dotStr=dotStr)

