from abc import abstractmethod
from typing import Optional, Any

from ..model.ExcelOntology import OntologyImport, ExcelOntology
from ..model.Result import Result


class OntologyBuildService:
    @abstractmethod
    def merge_imports(self,
                      imports: list[OntologyImport],
                      outfile: str,
                      iri: str,
                      main_ontology_name: str,
                      tmp_dir: str) -> Result[Any]:
        pass

    @abstractmethod
    def build_ontology(self,
                       ontology: ExcelOntology,
                       outfile: str,
                       prefixes: Optional[dict[str, str]],
                       dependency_iris: Optional[list[str]],
                       tmp_dir: str) -> Result[Any]:
        pass

    @abstractmethod
    def merge_ontologies(self,
                         ontologies: list[str],
                         outfile: str,
                         iri: str,
                         version_iri: str,
                         annotations: dict[str, str]) -> Result[Any]:
        pass
