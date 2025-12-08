import os
import pickle
from flask import Blueprint, current_app, g, json, request, jsonify
from flask_github import GitHub
import jsonschema
import networkx

from pydot import Dot

from ose.SpreadsheetSearcher import SpreadsheetSearcher
from ose.guards.with_permission import requires_permissions
from ose.model.Term import Term
from ose.model.ExcelOntology import ExcelOntology
from ose.model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ose.model.TermIdentifier import TermIdentifier
from ose.services.FileCache import FileCache
from ose.services.ConfigurationService import ConfigurationService
from ose.utils.github import get_file

bp = Blueprint("api_visualise", __name__, url_prefix="/api/visualise")

NODE_PROPS = {
    "shape": "box",
    "style": "rounded,filled",
    "fontname": "arial",
    "fillcolor": "white",
}
GRAPH_PROPS = {
    "rankdir": "BT",
    "bgcolor": "transparent",
    "splines": "true",
    "overlap": "false",
    "fontsize": "10",
    "labelloc": "t",
    "labeljust": "c",
    "fontname": "arial",
}
RELATION_COLOR_MAP = {
    "has part": "blue",
    "part of": "blue",
    "contains": "green",
    "has role": "darkgreen",
    "is about": "darkgrey",
    "has participant": "darkblue",
}


@bp.route("/generate/<string:repo>/<path:path>", methods=["POST"])
@requires_permissions("view")
def generate_visualisation(
    repo: str, path: str, config: ConfigurationService, cache: FileCache
):
    user_name = g.user.github_login if g.user else "*"
    user_repos = (
        config.app_config["USERS"]
        .get(user_name, config.app_config["USERS"].get("*", {}))
        .get("repositories", [])
    )

    if repo not in user_repos:
        return jsonify({"msg": f"No such repository '{repo}'", "success": False}), 404

    assert current_app.static_folder is not None
    schema: dict
    with open(
        os.path.join(current_app.static_folder, "schema", "req_body_visualise.json"),
        "r",
    ) as f:
        schema = json.load(f)

    data = request.json
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        return jsonify({"success": False, "error": f"Invalid format: {e}"}), 400

    assert data is not None

    # Load rows from request body
    rows: list[list[str]] = data.get("rows")
    header: list[str] = data.get("header")

    terms_iri = f"file:///tmp/{repo}/{path}"
    ontology = ExcelOntology(terms_iri)
    ontology.add_terms_from_list(rows, header, origin=path)

    # Load externals
    repository = config.get(repo)
    assert repository is not None

    release_script_json = json.loads(
        config.get_file(repository, repository.release_script_path)
    )
    release_script = ReleaseScript.from_json(release_script_json)
    externals_owl = config.get_file(repository, release_script.external.target.file)
    externals_ontology = ExcelOntology.from_owl(
        externals_owl, repository.prefixes, "dependency:" + release_script.external.target.file
    ).value

    # Load derived
    def get_derived(file: ReleaseScriptFile) -> list[ReleaseScriptFile]:
        name = next(n for n, f in release_script.files.items() if f == file)
        derived: list[ReleaseScriptFile] = [
            s for s in release_script.files.values() if name in s.needs
        ]

        return derived + [item for s in derived for item in get_derived(s)]

    release_script_file = next(
        f
        for n, f in release_script.files.items()
        if path in [s.file for s in f.sources]
    )
    derived = get_derived(release_script_file)
    derived = [
        d for i, d in enumerate(derived) if d not in derived[:i]
    ]  # Remove duplicates

    derived_ontology = ExcelOntology(terms_iri + "/derived")
    for der in derived:
        for source in der.sources:
            if source.type == "classes":
                xlsx = config.get_file_raw(repository, source.file)
                excel_ontology = ExcelOntology.from_excel(
                    source.file, [(source.file, xlsx, source.type)]
                )
                derived_ontology.merge(excel_ontology)
            elif source.type == "owl":
                owl_data = config.get_file(repository, source.file)
                owl_ontology = ExcelOntology.from_owl(
                    owl_data, repository.prefixes
                ).value
                derived_ontology.merge(owl_ontology)
                
    # Load dependencies
    def get_dependencies(file: ReleaseScriptFile) -> list[ReleaseScriptFile]:
        dependencies: list[ReleaseScriptFile] = [
            s for n, s in release_script.files.items() if n in file.needs
        ]

        return dependencies + [item for s in dependencies for item in get_dependencies(s)]

    dependencies = get_dependencies(release_script_file)
    dependencies = [
        d for i, d in enumerate(dependencies) if d not in dependencies[:i]
    ]  # Remove duplicates


    dependencies_ontology = ExcelOntology(terms_iri + "/dependencies")
    dependencies_ontology.merge(externals_ontology)
    for dep in dependencies:
        for source in dep.sources:
            if source.type == "classes":
                xlsx = config.get_file_raw(repository, source.file)
                excel_ontology = ExcelOntology.from_excel(
                    source.file, [("dependency:" + source.file, xlsx, source.type)]
                )
                dependencies_ontology.merge(excel_ontology)
            elif source.type == "owl":
                owl_data = config.get_file(repository, source.file)
                owl_ontology = ExcelOntology.from_owl(
                    owl_data, repository.prefixes, origin="dependency:" + source.file
                ).value
                dependencies_ontology.merge(owl_ontology)
                
    ontology.merge(dependencies_ontology)
    ontology.merge(derived_ontology)

    r = ontology.resolve()

    graph = visualise_ontology(ontology)

    # Generate visualisation data
    cache_data = pickle.dumps((graph, ontology, repo, path))
    cache_id = cache.store(
        f"visualisations_{repo}_{path.replace('/', '_')}.pkl", cache_data
    )

    return (
        jsonify(
            {"success": True, "visualisation_id": cache_id, "dot": graph.to_string()}
        ),
        200,
    )


def _get_node_properties_for_term(
    term: Term | TermIdentifier,
    curation_status: str | None = None,
    label: str | None = None,
    origin: str | None = None,
) -> dict:

    if isinstance(term, TermIdentifier):
        if label is None:
            if term.label is None:
                assert term.id is not None
                label = term.id
            else:
                label = term.label

        curation_status = curation_status or "unknown"
        origin = origin or "unknown"
    else:
        curation_status = curation_status or term.curation_status() or "unknown"
        origin = origin or (term.origin[0] if term.origin is not None else "<unknown>")
        label = label or term.label

    label = label.replace(" ", "\n")

    return {
        "ose_curation": curation_status,
        "ose_origin": origin,
        "class": f"ose-curation-status-{curation_status.lower().replace(' ', '_')}",
        "label": label
    }
    
    
    



def visualise_ontology(ontology: ExcelOntology) -> Dot:
    graph = networkx.MultiDiGraph()
    # graph.add_node("node", **NODE_PROPS)  # Set default node properties

    for term in ontology.terms():
        props = _get_node_properties_for_term(term)
        graph.add_node(term.id.replace(":", "_"), **props)

    for term in ontology.terms():
        for parent in term.sub_class_of:
            if not any(parent.id == t.id for t in ontology.terms()):
                props = _get_node_properties_for_term(
                    parent, curation_status="external"
                )
                graph.add_node(parent.id.replace(":", "_"), **props)

            graph.add_edge(
                parent.id.replace(":", "_"),
                term.id.replace(":", "_"),
                term.id.replace(":", "_"),
                type="subclass_of",
            )
            
            
    roots = [n for n in graph if graph.out_degree(n) == 0]
        

    node_data = graph.nodes(data=True)
    def visual_depth(node_id: str) -> int:
        """
        Calculate the visual depth of a node in the graph. Nodes that originate
        from dependencies have a depth of -1 unless they have children that do not
        originate from dependencies.
        
        :param n: Node in the graph
        :type n: networkx.classes.reportviews.NodeView
        :return: Depth of the node
        :rtype: int
        """
        depth = max((visual_depth(p) for p in graph.predecessors(node_id)), default=-1)
        origin: str | None = node_data[node_id]["ose_origin"]
        
        if not origin or origin.startswith("dependency:"):
            if any(not (node_data[s]['ose_origin'] and node_data[s]['ose_origin'].startswith("dependency:")) for s in graph.successors(node_id)):
                depth += 1
            else:
                return 0
        
        return depth
    
    for n in graph:
        graph.nodes[n]['visual_depth'] = visual_depth(n)

    
    for term in ontology.terms():
        for rel, target in term.relations:
            if rel.label:
                rcolor = RELATION_COLOR_MAP.get(rel.label, "orange")

                if isinstance(target, TermIdentifier):
                    if not any(target.id == t.id for t in ontology.terms()):
                        props = _get_node_properties_for_term(
                            target, curation_status="external"
                        )
                        graph.add_node(target.id.replace(":", "_"), **props)

                    graph.add_edge(
                        term.id.replace(":", "_"),
                        target.id.replace(":", "_"),
                        term.id.replace(":", "_"),
                        color=rcolor,
                        label=rel.label,
                        type=rel,
                    )

    dot = networkx.nx_pydot.to_pydot(graph)

    for k, v in GRAPH_PROPS.items():
        dot.set(k, v)

    return dot


@bp.route("/load/<string:visualisation_id>", methods=["GET"])
@requires_permissions("view")
def load_visualisation(visualisation_id: str, cache: FileCache):
    if visualisation_id is None or visualisation_id.strip() == "":
        return jsonify({"success": False, "error": "Invalid visualisation ID"}), 400

    cache_data = cache.retrieve(visualisation_id)
    if cache_data is None:
        return jsonify({"success": False, "error": "Visualisation not found"}), 404

    graph, ontology, repo, path = pickle.loads(cache_data)

    graph = visualise_ontology(ontology)

    return jsonify({"success": True, "dot": graph.to_string(), "repo": repo, "path": path}), 200
