from abc import abstractmethod, ABC
from typing import Optional, Any, Dict, List

from ..model.ExcelOntology import OntologyImport, ExcelOntology
from ..model.Result import Result


class OntologyBuildService(ABC):
    @abstractmethod
    def merge_imports(self,
                      imports: List[OntologyImport],
                      outfile: str,
                      iri: str,
                      main_ontology_name: str,
                      tmp_dir: str) -> Result[Any]:
        ...

    @abstractmethod
    def build_ontology(self,
                       ontology: ExcelOntology,
                       outfile: str,
                       prefixes: Optional[Dict[str, str]],
                       dependency_iris: Optional[List[str]],
                       tmp_dir: str) -> Result[Any]:
        ...

    @abstractmethod
    def merge_ontologies(self,
                         ontologies: List[str],
                         outfile: str,
                         iri: str,
                         version_iri: str,
                         annotations: Dict[str, str]) -> Result[Any]:
        ...

    @abstractmethod
    def collapse_imports(self, file: str) -> Result[Any]:
        ...