import dataclasses
import os
import tempfile
from typing import Optional, List, Tuple, Any, Callable, Dict

import openpyxl
import pyhornedowl
from flask import Blueprint, render_template, g, request, jsonify, current_app, redirect, url_for, send_file
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from openpyxl.worksheet.worksheet import Worksheet
from typing_extensions import Self
from werkzeug.exceptions import NotFound

from ..SpreadsheetSearcher import SpreadsheetSearcher
from ..database.Release import Release
from ..guards.admin import verify_admin
from ..services.OntoloyBuildService import OntologyBuildService
from ..utils import get_spreadsheets, get_spreadsheet, letters

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")


@bp.route("/")
@bp.route("/dashboard")
@verify_admin
def dashboard():
    return render_template("dashboard.html",
                           login=g.user.github_login,
                           breadcrumb=[{"name": "Admin", "path": "/admin/dashboard"}])


# Pages for the app
@bp.route("/rebuild-index", methods=("GET", "POST"))
@verify_admin
def rebuild_index(searcher: SpreadsheetSearcher):
    if request.method == "POST":
        sheets = searcher.rebuild_index()
        return jsonify(sheets)
    elif request.method == "GET":
        return render_template("rebuild_index.html",
                               index_stats=searcher.stats(),
                               breadcrumb=[
                                   dict(name="Admin", path="admin/dashboard"),
                                   dict(name="Rebuild index", path="admin/rebuild-index")
                               ],
                               login=g.user.github_login, )


def release_data(db: SQLAlchemy, id: Optional[int] = None, repo: Optional[str] = None) -> dict:
    if id is None:
        if repo is not None:
            current_release = db.session.query(Release).filter_by(running=True, repo=repo).first()
        else:
            current_release = None
    else:
        current_release = db.session.query(Release).get(id)
        if current_release is None:
            raise NotFound(f"Cannot find release with id '{id}'.")

    return dict(
        release=current_release,
        login=g.user.github_login,
    )


@bp.route("/release/", methods=("GET",), defaults={"repo": None, "id": None})
@bp.route("/release/<string:repo>", methods=("GET",), defaults={"id": None})
@bp.route("/release/<int:id>", methods=("GET",), defaults={"repo": None})
@verify_admin
def release(repo: Optional[str], id: Optional[int], db: SQLAlchemy):
    data = release_data(db, id, repo)

    current_release: Release = data["release"]
    repositories = None

    if id is None and repo is None:
        repositories = current_app.config['REPOSITORIES']

        user_repos = repositories.keys()
        # Filter just the repositories that the user can see
        if g.user.github_login in current_app.config['USERS_METADATA']:
            user_repos = current_app.config['USERS_METADATA'][g.user.github_login]["repositories"]

        repositories = {k: v for k, v in repositories.items() if k in user_repos}

        if len(repositories) == 1:
            return redirect(url_for("admin.release", repo=list(repositories.keys())[0]))
    elif id is None and repo is not None:
        if current_release is not None:
            return redirect(url_for("admin.release", id=current_release.id))
    elif id is not None and repo is None:
        if current_release is not None:
            repo = current_release.repo

    paths = [dict(name=repo.upper(), path=f"admin/release/{repo}") if repo is not None else None]

    return render_template("release.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Release", path="admin/release"),
                               *[p for p in paths if p is not None]
                           ],
                           repo=repo,
                           repos=repositories,
                           **data
                           )


@dataclasses.dataclass
class Node:
    item: str
    label: str
    definition: str
    children: List[Self] = dataclasses.field(default_factory=list)
    parent: Optional[Self] = None
    annotations: Dict[str, str] = dataclasses.field(default_factory=dict)

    def to_plain(self):
        plain_children = []
        for c in self.children:
            plain_children.append(c.to_plain())

        return dict(item=self.item, label=self.label, definition=self.definition, children=plain_children)

    def height(self) -> int:
        return max((c.height() for c in self.children), default=0) + 1

    def recurse(self, fn: Callable[[Self], Any]):
        fn(self)
        for c in self.children:
            c.recurse(fn)


def form_tree(edges: List[Tuple[Tuple[str, str, str], Optional[str]]]) -> List[Node]:
    all_nodes = set(n for n, _ in edges)
    item_to_node = dict((c, Node(item=c, label=l if l is not None else c, definition=d)) for (c, l, d) in all_nodes)

    for (child, _, _), parent in edges:
        if parent is None:
            continue

        if child == parent:
            continue

        child_node = item_to_node[child]
        parent_node = item_to_node.setdefault(parent, Node(item=parent, label=parent, definition=""))

        child_node.parent = parent_node
        parent_node.children.append(child_node)

    return [n for n in item_to_node.values() if n.parent is None]


@bp.route("/hierarchical-overview")
def hierarchical_overview():
    return render_template("hierarchical_overview.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Hierarchical overviews", path="admin/hierarchical-overview")
                           ])


@bp.route("/hierarchical-overview/download/<repo>", defaults={"sub_ontology": None} )
@bp.route("/hierarchical-overview/download/<repo>/<sub_ontology>")
def hierarchical_overview_download(gh: GitHub, ontology_builder: OntologyBuildService, repo: str, sub_ontology: Optional[str] = None):
    hierarchies, ontology = build_hierarchy(gh, ontology_builder, repo, sub_ontology)

    wb = openpyxl.Workbook()
    sheet: Worksheet = wb.active

    height = max(h.height() for h in hierarchies)
    annotations = list({k for h in hierarchies for k in h.annotations.keys() })

    sheet.append(["ID", "Label"] + [""] * (height - 1) + ["Definition"] + annotations)

    def write_line(n: Node, depth: int) -> None:
        sheet.append([ontology.get_id_for_iri(n.item)] +
                     [""] * depth +
                     [n.label] + [""] * (height - depth - 1) +
                     [n.definition] +
                     [n.annotations.get(a, None) for a in annotations])

        for child in n.children:
            write_line(child, depth + 1)

    for hierarchy in hierarchies:
        write_line(hierarchy, 0)

    with tempfile.NamedTemporaryFile("w") as f:
        wb.save(f.name)

        download_name = f"{repo}-hierarchy.xlsx" if sub_ontology is None else f"{repo}-{sub_ontology}-hierarchy.xlsx"
        return send_file(f.name, download_name=download_name)


def build_hierarchy(gh: GitHub, ontology_builder: OntologyBuildService, repo: str, sub_ontology: Optional[str] = None) -> Tuple[List[Node], pyhornedowl.PyIndexedOntology]:
    # Excel files to extract annotations
    excel_files: List[str]
    release_file: str
    full_repo = current_app.config["REPOSITORIES"][repo]

    if sub_ontology is not None:
        sub = current_app.config["SUB_ONTOLOGIES"].get(repo, dict()).get(sub_ontology, None)

        if sub is None:
            raise NotFound(f"No such sub-ontology '{sub_ontology}'")

        excel_files = [sub["excel_file"]]
        release_file = sub["release_file"]
    else:
        release_file = current_app.config["RELEASE_FILES"][repo]

        branch = current_app.config["DEFAULT_BRANCH"][repo]
        active_sheets = current_app.config["ACTIVE_SPREADSHEETS"][repo]
        regex = "|".join(f"({r})" for r in active_sheets)

        excel_files = get_spreadsheets(gh, full_repo, branch, include_pattern=regex)

    response = gh.get(f"repos/{full_repo}/contents/{release_file}",
                      headers={"Accept": "application/vnd.github.raw+json"})

    temp_file = tempfile.NamedTemporaryFile("r+b", suffix=".owl", delete=False)
    temp_file.write(response.content)
    temp_file.close()

    ontology_builder.collapse_imports(temp_file.name)

    with open(temp_file.name, "rb") as fr:
        ontology = pyhornedowl.open_ontology(fr.read().decode('utf-8'))

    os.unlink(temp_file.name)

    # ontology = pyhornedowl.open_ontology(response.content.decode('utf-8'))
    for p, d in current_app.config["PREFIXES"]:
        ontology.add_prefix_mapping(p, d)
    classes = [(c, ontology.get_annotation(c, "http://www.w3.org/2000/01/rdf-schema#label"),
                ontology.get_annotation(c, "http://purl.obolibrary.org/obo/IAO_0000115")) for c in
               ontology.get_classes()]
    child_parent: List[Tuple[Tuple[str, Optional[str], Optional[str]], Optional[str]]] = []
    for c in classes:
        for p in ontology.get_superclasses(c[0]):
            child_parent.append((c, p))
        else:
            child_parent.append((c, None))

    # child_parent = [(c, p) for c in classes for p in ontology.get_superclasses(c[0])]
    hierarchies = form_tree(child_parent)

    for excel_file in excel_files:
        _, rows, header = get_spreadsheet(gh, full_repo, "", excel_file)
        data = dict((r["ID"], r) for r in rows if "ID" in r)

        def annotate(n: Node):
            id = ontology.get_id_for_iri(n.item)
            fields = {
                "comment": "Comment",
                "subontology": "Sub-ontology",
                "examples": "Examples",
                "synonyms": "Synonyms",
                "crossreference": "Cross reference",
                "informaldefinition": "Informal definition",
            }
            for field_key, field in fields.items():
                node_data = data.get(id, dict())
                key = next((k for k in node_data.keys() if letters(k) == field_key), None)
                if n.annotations.get(field, None) is None:
                    n.annotations[field] = node_data.get(key, None)

        for h in hierarchies:
            h.recurse(annotate)

    return hierarchies, ontology
