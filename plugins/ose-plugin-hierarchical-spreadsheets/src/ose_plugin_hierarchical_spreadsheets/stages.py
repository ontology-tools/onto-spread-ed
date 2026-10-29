import re
from typing import Tuple

import networkx as nx

import openpyxl
import pyhornedowl
from ose.building.stages import BuildStage
from ose.building.Progress import ProgressManager
from ose.ontology.hierarchy import build_hierarchy
from ose.project import ProjectFile
from ose.result import Success
from ose.utils.asyncio import check_cancelled



class GenerateHierarchicalSpreadsheetStage(BuildStage):
    def __init__(self, step_config, context):
        super().__init__(step_config, context)
        self._included_files = self.config.args["included_files"]

    async def run(self, on_progress_update=None):

        files = [f for k, f in self.project.files.items() if k in self._included_files]
        progress = ProgressManager(on_progress_update, len(files))

        for file in files:
            await check_cancelled()
            progress.next_item(item=file.target.file, message="Generating hierarchical spreadsheet for")

            G, ontology = self.build_hierarchy(file)

            wb = openpyxl.Workbook()
            assert wb.active is not None
            sheet = wb.active

            height = nx.dag_longest_path_length(G) + 1 if len(G) else 1
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
            sub_name = re.sub(f"^{self.project.short_repository_name}[_]?", "", sub_name, flags=re.IGNORECASE)

            file_name = f"{self.project.short_repository_name}-{sub_name}-hierarchy.xlsx"

            wb.save(self._local_name(file_name))

            self.context.add_final_artifact(self._local_name(file_name), self.name(), f"{path}/{file_name}")
        
        
        return Success(())
        
        

    @classmethod
    def name(cls) -> str:
        return "HIERARCHICAL_SPREADSHEETS"

    def build_hierarchy(self, file: ProjectFile) -> Tuple[nx.DiGraph, pyhornedowl.PyIndexedOntology]:
        return build_hierarchy(file, self.context.artifacts, self._local_name, self.project.prefixes)
