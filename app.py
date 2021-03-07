# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
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

# [START gae_python37_app]
import os
import io
import functools
import openpyxl
from openpyxl.styles import Font
from openpyxl.styles import PatternFill
import base64
import json
import traceback
import daff

from flask import Flask, request, g, session, redirect, url_for, render_template
from flask import render_template_string, jsonify, Response
from flask_github import GitHub

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import threading

import whoosh
from whoosh.qparser import MultifieldParser

from datetime import datetime

# setup sqlalchemy

from config import *

engine = create_engine(DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    github_id = Column(Integer)
    github_login = Column(String(255))

    def __init__(self, github_access_token):
        self.github_access_token = github_access_token

def init_db():

    Base.query = db_session.query_property()
    Base.metadata.create_all(bind=engine)


# Create an app instance
class FlaskApp(Flask):
    def __init__(self, *args, **kwargs):
        super(FlaskApp, self).__init__(*args, **kwargs)
        self._activate_background_job()

    def _activate_background_job(self):
        init_db()


# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = FlaskApp(__name__)

app.config.from_object('config')

github = GitHub(app)


# Implementation of Google Cloud Storage for index
class BucketStorage(whoosh.filedb.filestore.RamStorage):
    def __init__(self, bucket):
        super().__init__()
        self.bucket = bucket
        self.filenameslist = []

    def save_to_bucket(self):
        for name in self.files.keys():
            with self.open_file(name) as source:
                print("Saving file",name)
                blob = self.bucket.blob(name)
                blob.upload_from_file(source)
        for name in self.filenameslist:
            if name not in self.files.keys():
                blob = self.bucket.blob(name)
                print("Deleting old file",name)
                self.bucket.delete_blob(blob.name)
                self.filenameslist.remove(name)

    def open_from_bucket(self):
        self.filenameslist = []
        for blob in bucket.list_blobs():
            print("Opening blob",blob.name)
            self.filenameslist.append(blob.name)
            f = self.create_file(blob.name)
            blob.download_to_file(f)
            f.close()


class SpreadsheetSearcher:
    # bucket is defined in config.py
    def __init__(self):
        self.storage = BucketStorage(bucket)
        self.threadLock = threading.Lock()

    def searchFor(self, repo_name, search_string):
        self.storage.open_from_bucket()
        ix = self.storage.open_index()

        mparser = MultifieldParser(["class_id","label","definition","parent"],
                                schema=ix.schema)

        query = mparser.parse("repo:"+repo_name+" AND ("+search_string+")")

        with ix.searcher() as searcher:
            results = searcher.search(query, limit=100)
            resultslist = []
            for hit in results:
                allfields = {}
                for field in hit:
                    allfields[field]=hit[field]
                resultslist.append(allfields)

        ix.close()

        return (resultslist)

    def updateIndex(self, repo_name, folder, sheet_name, header, sheet_data):
        self.threadLock.acquire()
        print("Updating index...")
        self.storage.open_from_bucket()
        ix = self.storage.open_index()
        writer = ix.writer()
        mparser = MultifieldParser(["repo", "spreadsheet"],
                                   schema=ix.schema)
        print("About to delete for query string: ","repo:" + repo_name + " AND spreadsheet:'" + folder+"/"+sheet_name+"'")
        writer.delete_by_query(
            mparser.parse("repo:" + repo_name + " AND spreadsheet:\"" + folder+"/"+sheet_name+"\""))
        writer.commit()

        writer = ix.writer()

        for r in range(len(sheet_data)):
            row = [v for v in sheet_data[r].values()]
            del row[0] # Tabulator-added ID column

            if "ID" in header:
                class_id = row[header.index("ID")]
            else:
                class_id = None
            if "Label" in header:
                label = row[header.index("Label")]
            else:
                label = None
            if "Definition" in header:
                definition = row[header.index("Definition")]
            else:
                definition = None
            if "Parent" in header:
                parent = row[header.index("Parent")]
            else:
                parent = None

            if class_id or label or definition or parent:
                writer.add_document(repo=repo_name,
                                    spreadsheet=folder+'/'+sheet_name,
                                    class_id=(class_id if class_id else None),
                                    label=(label if label else None),
                                    definition=(definition if definition else None),
                                    parent=(parent if parent else None))
        writer.commit(optimize=True)
        self.storage.save_to_bucket()
        ix.close()
        self.threadLock.release()
        print("Update of index completed.")

searcher = SpreadsheetSearcher()


def verify_logged_in(fn):
    """
    Decorator used to make sure that the user is logged in
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        # If the user is not logged in, then redirect him to the "logged out" page:
        if not g.user:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)

    return wrapped

# Pages:


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        #print("user-id in session: ",session['user_id'])
        g.user = User.query.get(session['user_id'])


@app.after_request
def after_request(response):
    db_session.remove()
    return response


@github.access_token_getter
def token_getter():
    user = g.user
    if user is not None:
        return user.github_access_token


@app.route('/github-callback')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('home')
    if access_token is None:
        print("Authorization failed.")
        return redirect(url_for('logout'))

    user = User.query.filter_by(github_access_token=access_token).first()
    if user is None:
        user = User(access_token)
    # Not necessary to get these details here
    # but it helps humans to identify users easily.
    g.user = user
    github_user = github.get('/user')
    user.github_id = github_user['id']
    user.github_login = github_user['login']
    user.github_access_token = access_token
    db_session.add(user)
    db_session.commit()

    session['user_id'] = user.id
    return redirect(next_url)


@app.route('/login')
def login():
    if session.get('user_id', None) is not None:
        session.pop('user_id',None) # Could be stale
    return github.authorize(scope="user,repo")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('loggedout'))

@app.route("/loggedout")
def loggedout():
    """
    Displays the page to be shown to logged out users.
    """
    return render_template("loggedout.html")


@app.route('/user')
@verify_logged_in
def user():
    return jsonify(github.get('/user'))



# Pages for the app


@app.route('/search', methods=['POST'])
@verify_logged_in
def search():
    searchTerm = request.form.get("inputText")
    repoName = request.form.get("repoName")

    searchResults = searchAcrossSheets(repoName, searchTerm)
    
    searchResultsTable = json.dumps(searchResults)
    # print(f'')
    # print(f'searchResultsTable: ')
    # print(searchResultsTable)

    return ( json.dumps({"message":"Success",
                             "searchResults": searchResultsTable}), 200 )
                             

@app.route('/')
@app.route('/home')
@verify_logged_in
def home():
    repositories = app.config['REPOSITORIES']
    user_repos = repositories.keys()
    # Filter just the repositories that the user can see
    if g.user.github_login in USERS_METADATA:
        user_repos = USERS_METADATA[g.user.github_login]["repositories"]

    repositories = {k:v for k,v in repositories.items() if k in user_repos}

    return render_template('index.html',
                           login=g.user.github_login,
                           repos=repositories)


@app.route('/repo/<repo_key>')
@app.route('/repo/<repo_key>/<path:folder_path>')
@verify_logged_in
def repo(repo_key, folder_path=""):
    repositories = app.config['REPOSITORIES']
    repo_detail = repositories[repo_key]
    directories = github.get(
        f'repos/{repo_detail}/contents/{folder_path}'
    )
    #print(directories)
    dirs = []
    spreadsheets = []
    for directory in directories:
        if directory['type']=='dir':
            dirs.append(directory['name'])
        elif directory['type']=='file' and '.xlsx' in directory['name']:
            spreadsheets.append(directory['name'])
    if g.user.github_login in USERS_METADATA:
        user_initials = USERS_METADATA[g.user.github_login]["initials"]
    else:
        print(f"The user {g.user.github_login} has no known metadata")
        user_initials = g.user.github_login[0:2]

    return render_template('repo.html',
                            login=g.user.github_login,
                            user_initials=user_initials,
                            repo_name = repo_key,
                            folder_path = folder_path,
                            directories = dirs,
                            spreadsheets = spreadsheets,
                            )

@app.route("/direct", methods=["POST"])
@verify_logged_in
def direct():
    if request.method == "POST":
        repo = json.loads(request.form.get("repo"))
        sheet = json.loads(request.form.get("sheet"))
        go_to_row = json.loads(request.form.get("go_to_row"))
    repoStr = repo['repo']
    sheetStr = sheet['sheet']
    url = '/edit' + '/' + repoStr + '/' + sheetStr 
    session['label'] = go_to_row['go_to_row']
    session['url'] = url
    return('success')

@app.route("/validate", methods=["POST"]) # cell, column, rowData, headers, table
@verify_logged_in
def verify():
    if request.method == "POST":
        cell = json.loads(request.form.get("cell"))
        column = json.loads(request.form.get("column"))
        rowData = json.loads(request.form.get("rowData"))
        headers = json.loads(request.form.get("headers")) 
        table = json.loads(request.form.get("table")) 
    # print('cell: ' + cell)    
    # print('column: ' + column)
    # print('rowData: ' + json.dumps(rowData)) 
    # print('headers: ' + json.dumps(headers))
    # print('table: ' + json.dumps(table))
    if column == "Label" or column == "ID" or column == "Definition":
        if checkNotUnique(cell, column, headers, table): #todo: checkNotUnique should return the message? Do we need more info in there?
            return ('Value is not unique')
    # test:
    # if cell == 'fail': 
    #     return ('fail message says you failed')
    return ('success') #todo: do we need message:success, 200 here? 
    
# validation checks here: 
def checkNotUnique(cell, column, headers, table):
    counter = 0
    print(len(cell))
    cellStr = cell.strip()
    print(cellStr)
    # if Label, ID or Definition column
    # check cell against all other cells in the same column
    # return true if same
    for r in range(len(table)): 
        row = [v for v in table[r].values()]
        del row[0] # remove extra numbered "id" column
        for c in range(len(headers)):
            if headers[c] == "ID" and column == "ID":
                if row[c].strip()==cellStr:
                    counter += 1 
                    if counter > 1: #more than one of the same
                        return True
            if headers[c] == "Label" and column == "Label":
                if row[c].strip()==cellStr:
                    counter += 1 
                    if counter > 1: 
                        return True
            if headers[c] == "Definition" and column == "Definition":
                if row[c].strip()==cellStr:
                    counter += 1 
                    if counter > 1: 
                        return True

    print(len(cellStr))
    return False

@app.route('/edit/<repo_key>/<path:folder>/<spreadsheet>')
@verify_logged_in
def edit(repo_key, folder, spreadsheet):
    if session.get('label') == None:
        go_to_row = ""
    else:
        go_to_row = session.get('label')
        session.pop('label', None)

    repositories = app.config['REPOSITORIES']
    repo_detail = repositories[repo_key]
    (file_sha,rows,header) = get_spreadsheet(repo_detail,folder,spreadsheet)
    if g.user.github_login in USERS_METADATA:
        user_initials = USERS_METADATA[g.user.github_login]["initials"]
    else:
        print(f"The user {g.user.github_login} has no known metadata")
        user_initials = g.user.github_login[0:2]

    return render_template('edit.html',
                            login=g.user.github_login,
                            user_initials=user_initials,
                            all_initials=ALL_USERS_INITIALS,
                            repo_name = repo_key,
                            folder = folder,
                            spreadsheet_name=spreadsheet,
                            header=json.dumps(header),
                            rows=json.dumps(rows),
                            file_sha = file_sha,
                            go_to_row = go_to_row
                            )


@app.route('/save', methods=['POST'])
@verify_logged_in
def save():
    repo_key = request.form.get("repo_key")
    folder = request.form.get("folder")
    spreadsheet = request.form.get("spreadsheet")
    row_data = request.form.get("rowData")
    initial_data = request.form.get("initialData")
    file_sha = request.form.get("file_sha").strip()
    commit_msg = request.form.get("commit_msg")
    commit_msg_extra = request.form.get("commit_msg_extra")
    overwrite = False
    overwriteVal = request.form.get("overwrite") #todo: get actual boolean value True/False here?
    print(f'overwriteVal is: ' + str(overwriteVal))
    if overwriteVal == "true":
        overwrite = True
        print(f'overwrite True here')

    repositories = app.config['REPOSITORIES']
    repo_detail = repositories[repo_key]

    try:
        initial_data_parsed = json.loads(initial_data)
        row_data_parsed = json.loads(row_data)
        # Get the data, skip the first 'id' column
        initial_first_row = initial_data_parsed[0]
        initial_header = [k for k in initial_first_row.keys()]
        del initial_header[0]
        # Sort based on label
        # What if 'Label' column not present?
        # todo: is sorting causing a problem with diff?
        if 'Label' in initial_first_row:
            initial_data_parsed = sorted(initial_data_parsed, key=lambda k: k['Label'] if k['Label'] else "")
        else:
            print("No Label column present, so not sorting this.") #do we need to sort - yes, for diff!

        first_row = row_data_parsed[0]
        header = [k for k in first_row.keys()]
        del header[0]
        # Sort based on label
        # What if 'Label' column not present?
        if 'Label' in first_row:
            row_data_parsed = sorted(row_data_parsed, key=lambda k: k['Label'] if k['Label'] else "")
        else:
            print("No Label column present, so not sorting this.") #do we need to sort - yes, for diff! 

        print("Got file_sha",file_sha)

        wb = openpyxl.Workbook()
        sheet = wb.active

        for c in range(len(header)):
            sheet.cell(row=1, column=c+1).value=header[c]
            sheet.cell(row=1, column=c+1).font = Font(size=12,bold=True)
        for r in range(len(row_data_parsed)):
            row = [v for v in row_data_parsed[r].values()]
            del row[0] # Tabulator-added ID column
            for c in range(len(header)):
                sheet.cell(row=r+2, column=c+1).value=row[c]
                # Set row background colours according to 'Curation status'
                # These should be kept in sync with those used in edit screen
                # TODO add to config
                # What if "Curation status" not present?
                if 'Curation status' in first_row:
                    if row[header.index("Curation status")]=="Discussed":
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="ffe4b5", fill_type = "solid")
                    elif row[header.index("Curation status")]=="Ready": #this is depreciated
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="98fb98", fill_type = "solid")
                    elif row[header.index("Curation status")]=="Proposed":
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="ffffff", fill_type = "solid")
                    elif row[header.index("Curation status")]=="To Be Discussed":
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="eee8aa", fill_type = "solid")
                    elif row[header.index("Curation status")]=="In Discussion":
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="fffacd", fill_type = "solid")                                
                    elif row[header.index("Curation status")]=="Published":
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="7fffd4", fill_type = "solid")
                    elif row[header.index("Curation status")]=="Obsolete":
                        sheet.cell(row=r+2, column=c+1).fill = PatternFill(fgColor="2f4f4f", fill_type = "solid")

        # Create version for saving
        spreadsheet_stream = io.BytesIO()
        wb.save(spreadsheet_stream)

        #base64_bytes = base64.b64encode(sample_string_bytes)
        base64_bytes = base64.b64encode(spreadsheet_stream.getvalue())
        base64_string = base64_bytes.decode("ascii")

        # Create a new branch to commit the change to (in case of simultaneous updates)
        response = github.get(f"repos/{repo_detail}/git/ref/heads/master")
        if not response or "object" not in response or "sha" not in response["object"]:
            raise Exception(f"Unable to get SHA for HEAD of master in {repo_detail}")
        sha = response["object"]["sha"]
        branch = f"{g.user.github_login}_{datetime.utcnow().strftime('%Y-%m-%d_%H%M%S')}"
        print("About to try to create branch in ",f"repos/{repo_detail}/git/refs")
        response = github.post(
            f"repos/{repo_detail}/git/refs", data={"ref": f"refs/heads/{branch}", "sha": sha},
            )
        if not response:
            raise Exception(f"Unable to create new branch {branch} in {repo_detail}")

        print("About to get latest version of the spreadsheet file",f"repos/{repo_detail}/contents/{folder}/{spreadsheet}")
        # Get the sha for the file
        (new_file_sha, new_rows, new_header) = get_spreadsheet(repo_detail,folder, spreadsheet)

        # Commit changes to branch (replace code with sheet)
        data = {
            "message": commit_msg,
            "content": base64_string,
            "branch": branch,
        }
        data["sha"] = new_file_sha
        print("About to commit file to branch",f"repos/{repo_detail}/contents/{folder}/{spreadsheet}")
        response = github.put(f"repos/{repo_detail}/contents/{folder}/{spreadsheet}", data=data)
        if not response:
            raise Exception(
                f"Unable to commit addition of {spreadsheet} to branch {branch} in {repo_detail}"
            )

        # Create a PR for the change
        print("About to create PR from branch",)
        response = github.post(
            f"repos/{repo_detail}/pulls",
            data={
                "title": commit_msg,
                "head": branch,
                "base": "master",
                "body": commit_msg_extra
            },
        )
        if not response:
            raise Exception(f"Unable to create PR for branch {branch} in {repo_detail}")
        pr_info = response['html_url']

        # Do not merge automatically if this file was stale as that will overwrite the other changes
        
        if new_file_sha != file_sha and not overwrite:
            print("PR created and must be merged manually as repo file had changed")

            # Get the changes between the new file and this one:
            merge_diff, merged_table = getDiff(row_data_parsed, new_rows, new_header, initial_data_parsed) # getDiff(saving version, latest server version, header for both)
            # update rows for comparison:
            (file_sha3,rows3,header3) = get_spreadsheet(repo_detail,folder,spreadsheet)
            return(
                json.dumps({'Error': 'Your change was submitted to the repository but could not be automatically merged due to a conflict. You can view the change <a href="'\
                    + pr_info + '" target = "_blank" >here </a>. ', "file_sha_1": file_sha, "file_sha_2": new_file_sha, "pr_branch":branch, "merge_diff":merge_diff, "merged_table":json.dumps(merged_table),\
                        "rows3": rows3, "header3": header3}), 300 #400 for missing REPO
                )
        else:
            # Merge the created PR
            print("About to merge created PR")
            response = github.post(
                f"repos/{repo_detail}/merges",
                data={
                    "head": branch,
                    "base": "master",
                    "commit_message": commit_msg
                },
            )
            if not response:
                raise Exception(f"Unable to merge PR from branch {branch} in {repo_detail}")

            # Delete the branch again
            print ("About to delete branch",f"repos/{repo_detail}/git/refs/heads/{branch}")
            response = github.delete(
                f"repos/{repo_detail}/git/refs/heads/{branch}")
            if not response:
                raise Exception(f"Unable to delete branch {branch} in {repo_detail}")

        print ("Save succeeded.")
        # Update the search index for this file ASYNCHRONOUSLY (don't wait)
        thread = threading.Thread(target=searcher.updateIndex,
                                  args=(repo_key, folder, spreadsheet, header, row_data_parsed))
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

        # Get the sha AGAIN for the file
        response = github.get(f"repos/{repo_detail}/contents/{folder}/{spreadsheet}")
        if not response or "sha" not in response:
            raise Exception(
                f"Unable to get the newly updated SHA value for {spreadsheet} in {repo_detail}/{folder}"
                )
        new_file_sha = response['sha']

        return ( json.dumps({"message":"Success",
                             "file_sha": new_file_sha}), 200 )

    except Exception as err:
        print(err)
        traceback.print_exc()
        return (
            json.dumps({"message": "Failed",
                        "Error":format(err)}),
            400,
        )


@app.route('/keepalive', methods=['POST'])
@verify_logged_in
def keep_alive():
    print("Keep alive requested from edit screen")
    return ( json.dumps({"message":"Success"}), 200 )


# Internal methods

def get_spreadsheet(repo_detail,folder,spreadsheet):
    spreadsheet_file = github.get(
        f'repos/{repo_detail}/contents/{folder}/{spreadsheet}'
    )
    file_sha = spreadsheet_file['sha']
    base64_bytes = spreadsheet_file['content'].encode('utf-8')
    decoded_data = base64.decodebytes(base64_bytes)
    wb = openpyxl.load_workbook(io.BytesIO(decoded_data))
    sheet = wb.active

    header = [cell.value for cell in sheet[1] if cell.value]
    rows = []
    for row in sheet[2:sheet.max_row]:
        values = {}
        for key, cell in zip(header, row):
            values[key] = cell.value
        if any(values.values()):
            rows.append(values)
    # print(f'rows: ')
    # print(json.dumps(rows))
    return ( (file_sha, rows, header) )


def getDiff(row_data_1, row_data_2, row_header, row_data_3): #(1saving, 2server, header, 3initial)

    # print(f'the type of row_data_3 is: ')
    # print(type(row_data_3))        

    #sort out row_data_1 format to be the same as row_data_2
    new_row_data_1 = []
    for k in row_data_1:
        dictT = {}
        for key, val, item in zip(k, k.values(), k.items()):
            if(key != "id"):
                if(val == ""):
                    val = None
                #add to dictionary:
                dictT[key] = val
        #add to list:
        new_row_data_1.append( dictT ) 

    #sort out row_data_3 format to be the same as row_data_2
    new_row_data_3 = []
    for h in row_data_3:
        dictT3 = {}
        for key, val, item in zip(h, h.values(), h.items()):
            if(key != "id"):
                if(val == ""):
                    val = None
                #add to dictionary:
                dictT3[key] = val
        #add to list:
        new_row_data_3.append( dictT3 ) 

    row_data_combo_1 = [row_header] 
    row_data_combo_2 = [row_header]
    row_data_combo_3 = [row_header]

    row_data_combo_1.extend([list(r.values()) for r in new_row_data_1]) #row_data_1 has extra "id" column for some reason???!!!
    row_data_combo_2.extend([list(s.values()) for s in row_data_2])
    row_data_combo_3.extend([list(t.values()) for t in new_row_data_3])

    #checking:
    # print(f'row_header: ')
    # print(row_header)
    # print(f'row_data_1: ')
    # print(row_data_1)
    # print(f'row_data_2: ')
    # print(row_data_2)
    # print(f'combined 1: ')
    # print(row_data_combo_1)
    # print(f'combined 2: ')
    # print(row_data_combo_2)
    # print(f'combined 3: ')
    # print(row_data_combo_3)

    table1 = daff.PythonTableView(row_data_combo_1) #daff needs a header in order to work correctly!
    table2 = daff.PythonTableView(row_data_combo_2)
    table3 = daff.PythonTableView(row_data_combo_3)
    
    #old version:
    # table1 = daff.PythonTableView([list(r.values()) for r in row_data_1])
    # table2 = daff.PythonTableView([list(r.values()) for r in row_data_2])

    alignment = daff.Coopy.compareTables3(table3,table2,table1).align() #3 way: initial vs server vs saving
    
    # alignment = daff.Coopy.compareTables(table3,table2).align() #initial vs server
    alignment2 = daff.Coopy.compareTables(table2,table1).align() #saving vs server
    # alignment2 = daff.Coopy.compareTables(table1, table2).align() #server vs saving
    # alignment = daff.Coopy.compareTables(table3,table1).align() #initial vs saving


    data_diff = []
    table_diff = daff.PythonTableView(data_diff)

    flags = daff.CompareFlags()

    # flags.allowDelete()
    # flags.allowUpdate()
    # flags.allowInsert()

    highlighter = daff.TableDiff(alignment2,flags)
    
    highlighter.hilite(table_diff)
    #hasDifference() should return true - and it does. 
    if highlighter.hasDifference():
        print(f'HASDIFFERENCE')
        print(highlighter.getSummary().row_deletes)
    else:
        print(f'no difference found')
    diff2html = daff.DiffRender()
    diff2html.usePrettyArrows(False)
    diff2html.render(table_diff)
    table_diff_html = diff2html.html()

    # print(table_diff_html)
    # print(f'table 1 before patch test: ')
    # print(table1.toString()) 
    # patch test: 
    # patcher = daff.HighlightPatch(table2,table_diff)
    # patcher.apply()
    # print(f'patch tester: ..................')
    # print(f'table1:')
    # print(table1.toString())
    # print(f'table2:')
    # print(table2.toString())
    # print(table2.toString()) 
    # print(f'table3:')
    # print(table3.toString()) 
    # table2String = table2.toString().strip() #no
    #todo: Task 1: turn MergeData into a Dict in order to post it to Github!
    # - use Janna's sheet builder example? 
    # - post direct instead of going through Flask front-end? 
    # table2String.strip()
    # table2Json = json.dumps(table2)
    # table2Dict = dict(todo: make this into a dict with id:0++ per row here!)
    # table2String = dict(table2String) #nope

    # merger test: 
    # print(f'Merger test: ') 
    merger = daff.Merger(table3,table2,table1,flags) #(3initial, 1saving, 2server, flags)
    merger.apply()
    # print(f'table2:')
    # table2String = table2.toString()
    # print(table2String) #after merger

    data = table2.getData() #merger table in list format
    # print(f'data: ')
    # print(json.dumps(data)) #it's a list.
    # convert to correct format (list of dicts):
    dataDict = []
    iter = -1
    for k in data:        
        # add "id" value:
        iter = iter + 1
        dictT = {}
        if iter == 0:
            pass
            # print(f'header row - not using')
        else:
            dictT['id'] = iter # add "id" with iteration
            for key, val in zip(row_header, k):      
                #deal with conflicting val?

                dictT[key] = val
        # add to list:
        if iter > 0: # not header - now empty dict
            dataDict.append( dictT ) 
        # print(f'update: ')
        # print(dataDict)

        
    
    # print(f'dataDict: ')
    # print(json.dumps(dataDict))
    # print(f'the type of dataDict is: ')
    # print(type(dataDict))

    # print(f'merger data:') #none
    # print(daff.DiffSummary().different) #nothing here? 
    # mergerConflictInfo = merger.getConflictInfos()
    
    # print(f'Merger conflict infos: ')
    # print(f'table1:')
    # print(table1.toString())
    # print(f'table2:')
    # print(table2.toString()) 
    # print(f'table3:')
    # print(table3.toString()) 
   
    return (table_diff_html, dataDict)


def searchAcrossSheets(repo_name, search_string):
    searcherAllResults = searcher.searchFor(repo_name, search_string)
    # print(searcherAllResults)
    return searcherAllResults



if __name__ == "__main__":        # on running python app.py

    app.run(debug=app.config["DEBUG"], port=8080)        # run the flask app




# [END gae_python37_app]
