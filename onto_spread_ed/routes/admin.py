import dataclasses
import tempfile
from typing import Optional, List, Tuple

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

bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="../templates/admin")


@bp.route("/")
@bp.route("/dashboard")
@verify_admin
def dashboard():
    return render_template("dashboard.html",
                           login=g.user.github_login,
                           breadcrumb=[{"name": "Admin", "path": "admin/dashboard"}])


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

    def to_plain(self):
        plain_children = []
        for c in self.children:
            plain_children.append(c.to_plain())

        return dict(item=self.item, label=self.label, definition=self.definition, children=plain_children)

    def height(self) -> int:
        return max((c.height() for c in self.children), default=0) + 1


def form_tree(edges: List[Tuple[Tuple[str, str, str], str]]) -> List[Node]:
    all_nodes = set(n for n, _ in edges)
    item_to_node = dict((c, Node(item=c, label=l, definition=d)) for (c, l, d) in all_nodes)

    for (child, _, _), parent in edges:
        if child == parent:
            continue

        child_node = item_to_node[child]
        parent_node = item_to_node.setdefault(parent, Node(item=parent, label=parent, definition=""))

        child_node.parent = parent_node
        parent_node.children.append(child_node)

    return [n for n in item_to_node.values() if n.parent is None]


@bp.route("/hierarchical-overview")
def hierarchical_overview(gh: GitHub):
    repo = request.args.get("repo")

    ontology = None
    hierarchies = []

    if repo is not None:
        hierarchies, ontology = build_hierarchy(gh, repo)

    return render_template("hierarchical_overview.html",
                           breadcrumb=[
                               dict(name="Admin", path="admin/dashboard"),
                               dict(name="Hierarchical overviews", path="admin/hierarchical-overview")
                           ],
                           ontology=ontology,
                           repo=repo,
                           hierarchies=[h.to_plain() for h in hierarchies])


@bp.route("/hierarchical-overview/download/<repo>")
def hierarchical_overview_download(gh: GitHub, repo: str):
    hierarchies, ontology = build_hierarchy(gh, repo)

    wb = openpyxl.Workbook()
    sheet: Worksheet = wb.active

    height = max(h.height() for h in hierarchies)

    sheet.append(["ID", "Label"] + [""] * (height - 1) + ["Definition"])

    def write_line(n: Node, depth: int) -> None:
        sheet.append([ontology.get_id_for_iri(n.item)] +
                     [""] * depth +
                     [n.label] + [""] * (height - depth - 1) +
                     [n.definition])

        for child in n.children:
            write_line(child, depth + 1)

    for hierarchy in hierarchies:
        write_line(hierarchy, 0)

    with tempfile.NamedTemporaryFile("w") as f:
        wb.save(f.name)

        return send_file(f.name, download_name=f"{repo}-hierarchy.xlsx")


def build_hierarchy(gh: GitHub, repo: str) -> Tuple[List[Node], pyhornedowl.PyIndexedOntology]:
    release_file = current_app.config["RELEASE_FILES"][repo]
    full_repo = current_app.config["REPOSITORIES"][repo]
    response = gh.get(f"repos/{full_repo}/contents/{release_file}",
                      headers={"Accept": "application/vnd.github.raw+json"})
    ontology = pyhornedowl.open_ontology(response.content.decode('utf-8'))
    for p, d in current_app.config["PREFIXES"]:
        ontology.add_prefix_mapping(p, d)
    classes = [(c, ontology.get_annotation(c, "http://www.w3.org/2000/01/rdf-schema#label"),
                ontology.get_annotation(c, "http://purl.obolibrary.org/obo/IAO_0000115")) for c in
               ontology.get_classes()]
    child_parent = [(c, p) for c in classes for p in ontology.get_superclasses(c[0])]
    hierarchies = form_tree(child_parent)
    return hierarchies, ontology
