import dataclasses
from typing import List, Optional, Dict, Callable, Any, Tuple

import pyhornedowl
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from typing_extensions import Self
from werkzeug.exceptions import NotFound

from .ReleaseStep import ReleaseStep
from ..model.ExcelOntology import ExcelOntology
from ..model.ReleaseScript import ReleaseScript
from ..model.Result import Result
from ..services.ConfigurationService import ConfigurationService
from ..utils import get_spreadsheets, get_spreadsheet, letters


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


class BuildReleaseStep(ReleaseStep):

    def __init__(self, db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int, tmp: str,
                 config: ConfigurationService, *, files: Dict[str, str]) -> None:
        super().__init__(db, gh, release_script, release_id, tmp, config)

        self._files = files

    def run(self) -> bool:
        result = Result(())

        self.build_

        self._total_items = len(sources)

        loaded = dict()
        for i, (k, file) in enumerate(sources):
            self._next_item()
            ontology = ExcelOntology(file.target.iri)

            external_ontology_result = self.load_externals_ontology()

            self._raise_if_canceled()

            result += external_ontology_result
            ontology.import_other_excel_ontology(external_ontology_result.value)

            self._raise_if_canceled()

            for n in file.needs:
                other = loaded[n]  # Must exist queue is ordered to first load ontologies others depend on
                result += ontology.import_other_excel_ontology(other)

                self._raise_if_canceled()

            for s in file.sources:
                if s.type == "classes":
                    result += ontology.add_terms_from_excel(s.file, self._local_name(s.file))
                elif s.type == "relations":
                    result += ontology.add_relations_from_excel(s.file, self._local_name(s.file))

            if file.renameTermFile is not None:
                ontology.apply_renamings(self._local_name(file.renameTermFile))

            if file.addParentsFile is not None:
                ontology.apply_new_parents(self._local_name(file.addParentsFile))

            result += ontology.resolve()
            self._raise_if_canceled()

            dependencies = [f for f in (
                    [self._release_script.files[n].target.iri for n in file.needs] +
                    [self._release_script.external.target.iri])]

            result += builder.build_ontology(ontology, self._local_name(file.target.file),
                                             self._release_script.prefixes, dependencies, self._working_dir,
                                             self._release_script.iri_prefix)
            self._raise_if_canceled()

            loaded[k] = ontology

        result.warnings = []
        self._set_release_result(result)
        return result.ok()

    @classmethod
    def name(cls) -> str:
        return "BUILD"

    def build_hierarchy(self, sub_ontology: Optional[str] = None) -> Tuple[
        List[Node], pyhornedowl.PyIndexedOntology]:
        # Excel files to extract annotations
        excel_files: List[str]
        release_file: str
        repository = config.get(repo)
        full_repo = repository.full_name

        excel_files = [f for f in self._release_script.files]

        if sub_ontology is not None:
            sub = repository.subontologies.get(sub_ontology, None)

            if sub is None:
                raise NotFound(f"No such sub-ontology '{sub_ontology}'")

            excel_files = [sub.excel_file]
            release_file = sub.release_file
        else:
            release_file = repository.release_file

            branch = repository.main_branch
            active_sheets = repository.indexed_files
            regex = "|".join(f"({r})" for r in active_sheets)

            excel_files = get_spreadsheets(gh, full_repo, branch, include_pattern=regex)

        response = gh.get(f"repos/{full_repo}/contents/{release_file}",
                          headers={"Accept": "application/vnd.github.raw+json"})

        ontology = pyhornedowl.open_ontology(response.content.decode('utf-8'), "rdf")

        # ontology = pyhornedowl.open_ontology(response.content.decode('utf-8'))
        for p, d in repository.prefixes.items():
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
