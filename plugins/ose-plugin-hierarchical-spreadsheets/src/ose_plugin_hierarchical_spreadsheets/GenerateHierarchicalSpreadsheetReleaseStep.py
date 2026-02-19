import dataclasses
import re
from typing import List, Optional, Dict, Callable, Any, Tuple

import networkx as nx

import openpyxl
import pyhornedowl
from typing_extensions import Self

from ose.release.ReleaseContext import ReleaseContext
from ose.release.ReleaseStep import ReleaseStep
from ose.model.ReleaseScript import ReleaseScriptFile
from ose.model.Result import Result

from ose.model.ExcelOntology import ExcelOntology
from ose.model.TermIdentifier import TermIdentifier


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


def form_tree(edges: List[Tuple[Tuple[str, str | None, str | None], Optional[str]]]) -> List[Node]:
    all_nodes = set(n for n, _ in edges)
    item_to_node = dict(
        (c, Node(item=c, label=lbl if lbl is not None else c, definition=d or "<no definition>"))
        for (c, lbl, d) in all_nodes
    )

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


class GenerateHierarchicalSpreadsheetReleaseStep(ReleaseStep):
    def __init__(
        self,
        context: ReleaseContext,
        *,
        included_files: Dict[str, str],
    ) -> None:
        super().__init__(context)

        self._included_files = included_files

    def run(self) -> bool:
        result = Result(())

        files = [f for k, f in self._release_script.files.items() if k in self._included_files]
        self._total_items = len(files)

        for file in files:
            self._next_item(item=file.target.file, message="Generating hierarchical spreadsheet for")

            G, ontology = self.build_hierarchy(file)

            wb = openpyxl.Workbook()
            assert wb.active is not None
            sheet = wb.active

            height = nx.dag_longest_path_length(G) + 1
            # height = max(h.height() for h in hierarchies)
            annotations = list(
                {
                    k
                    for n, d in G.nodes(data=True)
                    for k in d.keys() if k not in {"label", "definition"}
                }
            )
            # annotations = list({k for h in hierarchies for k in h.annotations.keys()})

            sheet.append(["ID", "Label"] + [""] * (height - 1) + ["Definition"] + annotations)

            def write_line(n: str, d: dict, depth: int) -> None:
                sheet.append(
                    [ontology.get_id_for_iri(n)]
                    + [""] * depth
                    + [d.get("label", n)]
                    + [""] * (height - depth - 1)
                    + [d.get("definition", "")]
                    + [d.get(a, None) for a in annotations]
                )

            roots = [(n, d) for n, d in G.nodes(data=True) if G.in_degree(n) == 0]
            for root, root_data in roots:
                write_line(root, root_data, 0)
                successors = nx.dfs_preorder_nodes(G, root)
                for c in successors:
                    d = G.nodes[c]
                    write_line(c, d, nx.shortest_path_length(G, root, c))

            [path, name] = file.target.file.rsplit("/", 1)
            sub_name = name.rsplit(".", 1)[0]
            sub_name = re.sub(f"^{self._release_script.short_repository_name}[_]?", "", sub_name, flags=re.IGNORECASE)

            file_name = f"{self._release_script.short_repository_name}-{sub_name}-hierarchy.xlsx"

            wb.save(self._local_name(file_name))

            self._store_artifact(self._local_name(file_name), f"{path}/{file_name}")
        
        
        self._set_release_result(result)
        return result.ok()
        
        

    @classmethod
    def name(cls) -> str:
        return "HIERARCHICAL_SPREADSHEETS"

    def build_hierarchy(self, file: ReleaseScriptFile) -> Tuple[nx.DiGraph, pyhornedowl.PyIndexedOntology]:
        release_file: str

        release_file = next(
            (a.local_path for a in self._artifacts() if a.target_path == file.target.file and a.kind == "final"),
            self._local_name(file.target.file),
        )

        ontology = pyhornedowl.open_ontology_from_file(release_file)

        for p, d in self._repo_config.prefixes.items():
            ontology.prefix_mapping.add_prefix(p, d)

        classes = [
            (
                c,
                ontology.get_annotation(c, "http://www.w3.org/2000/01/rdf-schema#label"),
                ontology.get_annotation(c, "http://purl.obolibrary.org/obo/IAO_0000115"),
            )
            for c in ontology.get_classes()
        ]
        child_parent: List[Tuple[Tuple[str, Optional[str], Optional[str]], Optional[str]]] = []
        for c in classes:
            for p in ontology.get_superclasses(c[0]):
                child_parent.append((c, p))
            else:
                child_parent.append((c, None))

        excel_ontology = ExcelOntology(file.target.iri)
        for s in file.sources:
            if s.type == "classes":
                excel_ontology.add_terms_from_excel(s.file, self._local_name(s.file)).ok_or_raise()
            elif s.type == "relations":
                excel_ontology.add_relations_from_excel(s.file, self._local_name(s.file)).ok_or_raise()

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
        G.add_nodes_from([(iri, {**node_annotations(iri), "label": label, "definition": definition}) for iri, label, definition in classes])
        G.add_edges_from([(p, c) for (c, _, _), p in child_parent if p is not None])
        
        # The only terms that should be included. All other may only be included if they are on a path from root to one of these terms.
        required_leaf_terms = {ontology.get_iri_for_id(t.id) for t in excel_ontology._terms if t.id is not None}
        
        # Remove all other nodes (e.g. external or from a higher level ontology)
        for root in [n for n in G if G.in_degree(n) == 0]:
            for n in list(nx.dfs_postorder_nodes(G, root)):
                if G.out_degree(n) == 0 and n not in required_leaf_terms:
                    G.remove_node(n)
        
        return G, ontology
