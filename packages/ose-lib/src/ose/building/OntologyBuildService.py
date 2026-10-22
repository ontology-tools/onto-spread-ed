from abc import abstractmethod, ABC
from typing import Optional, Any, Dict, List, Tuple, Literal

from ose.ontology import OntologyImport, ExcelOntology
from ose.result import Result


class OntologyBuildService(ABC):
    @abstractmethod
    async def merge_imports(
        self,
        imports: List[OntologyImport],
        outfile: str,
        iri: str,
        main_ontology_name: str,
        renamings: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
        new_parents: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
    ) -> Result[Any]:
        """Builds the external ontology `outfile` from the terms imported from other ontologies"""
        ...

    @abstractmethod
    async def build_ontology(self,
                       ontology: ExcelOntology,
                       outfile: str,
                       prefixes: Optional[Dict[str, str]],
                       dependency_iris: Optional[List[str]],
                       local_ontologies: Dict[str, str],
                       iri_prefix: str) -> Result[Any]:
        """
        Builds `outfile` from `ontology`.

        :param dependency_iris: IRIs of the ontologies that `ontology` imports. Each must be in `local_ontologies`.
        :param local_ontologies: IRIs of the ontologies of the build mapped to their local files. Imports of these IRIs,
            also by the dependencies, are resolved to the files instead of the published versions.
        """
        ...

    @abstractmethod
    async def merge_ontologies(self,
                         ontologies: List[str],
                         outfile: str,
                         iri: str,
                         version_iri: str,
                         annotations: Dict[str, str]) -> Result[Any]:
        ...

    @abstractmethod
    async def collapse_imports(self, file: str) -> Result[Any]:
        ...
