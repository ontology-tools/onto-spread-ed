import re
from typing import Dict, Tuple

import networkx as nx

import openpyxl
import pyhornedowl
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy

from ose.release.ReleaseStep import ReleaseStep
from ose.release.hierarchy import build_hierarchy as _build_hierarchy
from ose.model.ReleaseScript import ReleaseScript, ReleaseScriptFile
from ose.model.Result import Result
from ose.services.ConfigurationService import ConfigurationService


class GenerateHierarchicalSpreadsheetReleaseStep(ReleaseStep):
    def __init__(
        self,
        db: SQLAlchemy,
        gh: GitHub,
        release_script: ReleaseScript,
        release_id: int,
        tmp: str,
        config: ConfigurationService,
        *,
        included_files: Dict[str, str],
    ) -> None:
        super().__init__(db, gh, release_script, release_id, tmp, config)

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
        return _build_hierarchy(file, self._artifacts(), self._local_name, self._repo_config.prefixes)
