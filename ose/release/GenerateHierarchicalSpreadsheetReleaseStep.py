import dataclasses
import re
from typing import List, Optional, Dict, Callable, Any, Tuple

import openpyxl
import pyhornedowl
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from openpyxl.worksheet.worksheet import Worksheet
from typing_extensions import Self

from .ReleaseStep import ReleaseStep
from ..model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..utils import letters
from ..utils.github import parse_spreadsheet


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


class GenerateHierarchicalSpreadsheetReleaseStep(ReleaseStep):

    def __init__(self, db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int, tmp: str,
                 config: ConfigurationService, *, included_files: Dict[str, str]) -> None:
        super().__init__(db, gh, release_script, release_id, tmp, config)

        self._included_files = included_files

    def run(self) -> bool:
        result = Result(())

        files = [f for k, f in self._release_script.files.items() if k in self._included_files]
        self._total_items = len(files)

        for file in files:
            self._next_item(item=file.target.file, message="Generating hierarchical spreadsheet for")

            hierarchies, ontology = self.build_hierarchy(file)

            wb = openpyxl.Workbook()
            sheet: Worksheet = wb.active

            height = max(h.height() for h in hierarchies)
            annotations = list({k for h in hierarchies for k in h.annotations.keys()})

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

            [path, name] = file.target.file.rsplit("/", 1)
            sub_name = name.rsplit(".", 1)[0]
            sub_name = re.sub(f"^{self._release_script.short_repository_name}[_]?", "", sub_name, flags=re.IGNORECASE)

            file_name = f"{self._release_script.short_repository_name}-{sub_name}-hierarchy.xlsx"

            wb.save(self._local_name(file_name))

            self.store_artifact(self._local_name(file_name), f"{path}/{file_name}")

        result.warnings = []
        self._set_release_result(result)
        return result.ok()

    @classmethod
    def name(cls) -> str:
        return "HIERARCHICAL_SPREADSHEETS"

    def build_hierarchy(self, file: ReleaseScriptFile) -> Tuple[List[Node], pyhornedowl.PyIndexedOntology]:
        # Excel files to extract annotations
        excel_files: List[str]
        release_file: str

        excel_files = [self._local_name(s.file) for s in file.sources]
        release_file = self._local_name(file.target.file)

        ontology = pyhornedowl.open_ontology_from_file(release_file)

        for p, d in self._repo_config.prefixes.items():
            ontology.prefix_mapping.add_prefix(p, d)

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

        # If we do not collapse (or do not import) imported ontologies a root will always contain no label
        # We remove these roots as they only indicate where the subontology should be mounted in the overall ontology
        hierarchies = [c for h in hierarchies for c in h.children]

        for excel_file in excel_files:
            with open(excel_file, "rb") as f:
                file_data = f.read()

            rows, header = parse_spreadsheet(file_data)

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
