from typing import Callable, Optional

import networkx as nx
import pyhornedowl

from ..database.Release import ReleaseArtifact
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScriptFile
from ..model.TermIdentifier import TermIdentifier


def build_hierarchy(
    file: ReleaseScriptFile,
    artifacts: list[ReleaseArtifact],
    local_name_fn: Callable[[str], str],
    prefixes: dict[str, str],
) -> tuple[nx.DiGraph, pyhornedowl.PyIndexedOntology]:
    """Build a hierarchy graph and ontology from a release script file.

    Loads the OWL ontology for the given file, extracts class hierarchy
    information, and returns a pruned directed graph containing only
    terms defined in the source spreadsheets plus any ancestors on
    paths to those terms.

    Args:
        file: The release script file definition (sources + target).
        artifacts: Release artifacts from previous steps (used to find built OWL files).
        local_name_fn: Function mapping remote file paths to local paths.
        prefixes: IRI prefix mappings to register with the ontology.

    Returns:
        A tuple of (DiGraph, PyIndexedOntology). The graph has nodes with
        attributes ``label``, ``definition``, and optional annotation keys.
    """
    release_file: str = next(
        (a.local_path for a in artifacts if a.target_path == file.target.file and a.kind == "final"),
        local_name_fn(file.target.file),
    )

    ontology = pyhornedowl.open_ontology_from_file(release_file)

    for p, d in prefixes.items():
        ontology.prefix_mapping.add_prefix(p, d)

    classes = [
        (
            c,
            ontology.get_annotation(c, "http://www.w3.org/2000/01/rdf-schema#label"),
            ontology.get_annotation(c, "http://purl.obolibrary.org/obo/IAO_0000115"),
        )
        for c in ontology.get_classes()
    ]
    child_parent: list[tuple[tuple[str, Optional[str], Optional[str]], Optional[str]]] = []
    for c in classes:
        for p in ontology.get_superclasses(c[0]):
            child_parent.append((c, p))
        else:
            child_parent.append((c, None))

    excel_ontology = ExcelOntology(file.target.iri)
    for s in file.sources:
        if s.type == "classes":
            excel_ontology.add_terms_from_excel(s.file, local_name_fn(s.file)).ok_or_raise()
        elif s.type == "relations":
            excel_ontology.add_relations_from_excel(s.file, local_name_fn(s.file)).ok_or_raise()

    def node_annotations(iri: str) -> dict[str, str | None]:
        id = ontology.get_id_for_iri(iri)
        if id is None:
            return dict()

        term = excel_ontology._raw_term_by_id(id)
        if term is None or isinstance(term, TermIdentifier):
            return dict()

        return {
            "comment": term.get_relation_value(TermIdentifier(id="rdfs:comment")),
            "subontology": term.get_relation_value(TermIdentifier(label="lowerLevelOntology")),
            "examples": "; ".join(term.get_relation_values(TermIdentifier(id="IAO:0000112"))),
            "synonyms": "; ".join(term.get_relation_values(TermIdentifier(id="IAO:0000118"))),
            "crossreference": "; ".join(term.get_relation_values(TermIdentifier(label="crossReference"))),
            "informaldefinition": term.get_relation_value(TermIdentifier(label="informalDefinition")),
        }

    G = nx.DiGraph()
    G.add_nodes_from(
        [(iri, {**node_annotations(iri), "label": label, "definition": definition}) for iri, label, definition in classes]
    )
    G.add_edges_from([(p, c) for (c, _, _), p in child_parent if p is not None])

    # The only terms that should be included. All other may only be included if they are on a path from root to one of these terms.
    required_leaf_terms = {ontology.get_iri_for_id(t.id) for t in excel_ontology._terms if t.id is not None}

    # Remove all other nodes (e.g. external or from a higher level ontology)
    for root in [n for n in G if G.in_degree(n) == 0]:
        for n in list(nx.dfs_postorder_nodes(G, root)):
            if G.out_degree(n) == 0 and n not in required_leaf_terms:
                G.remove_node(n)

    return G, ontology
