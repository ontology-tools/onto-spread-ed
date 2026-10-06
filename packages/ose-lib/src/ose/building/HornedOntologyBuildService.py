from typing import Any, Dict, List, Literal, Tuple

from ose.ontology import ExcelOntology, OntologyImport
from ose.result import Result, Success, is_successful

from ose.building.OntoloyBuildService import OntologyBuildService

import pyhornedowl as ho
import pyhornedowl.model as hom


class HornedOntologyBuildService(OntologyBuildService):
    async def merge_imports(
        self,
        imports: List[OntologyImport],
        outfile: str,
        iri: str,
        main_ontology_name: str,
        tmp_dir: str,
        renamings: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
        new_parents: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
    ) -> Result[Any]:
        raise NotImplementedError

    async def build_ontology(
        self,
        ontology: ExcelOntology,
        outfile: str,
        prefixes: Dict[str, str] | None,
        dependency_iris: List[str] | None,
        tmp_dir: str,
        iri_prefix: str,
    ) -> Result[Any]:
        result = ontology.to_owl(prefixes if prefixes is not None else {})

        if not is_successful(result):
            return result

        result.value.save_to_file(outfile)

        return result

    async def merge_ontologies(
        self,
        ontologies: List[str],
        outfile: str,
        iri: str,
        version_iri: str,
        annotations: Dict[str, str],
    ) -> Result[Any]:
        o = ho.PyIndexedOntology()
        o.add_component(hom.OntologyID(o.iri(iri), o.iri(version_iri) if version_iri else None))
        
        for path in ontologies:
            ontology = ho.open_ontology_from_file(path)
            for c in ontology.get_components():
                if isinstance(c.component, hom.OntologyID):
                    continue  # keep the merged ontology's own ID
                o.add_component(c.component, c.ann)

        o.save_to_file(outfile)

        return Success(o)

    async def collapse_imports(self, file: str) -> Result[Any]:
        raise NotImplementedError
