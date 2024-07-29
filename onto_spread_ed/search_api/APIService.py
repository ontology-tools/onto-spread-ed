import abc
from typing import Tuple, List

from onto_spread_ed.model.ExcelOntology import ExcelOntology
from onto_spread_ed.model.Result import Result
from onto_spread_ed.services.ConfigurationService import ConfigurationService


class APIService(abc.ABC):
    _config: ConfigurationService

    def __init__(self, config: ConfigurationService):
        self._config = config

    @abc.abstractmethod
    def update_api(self, ontology: ExcelOntology, external_ontologies: List[str], revision_message: str) -> \
            Result[Tuple]:
        ...
