import abc
from typing import Tuple

from onto_spread_ed.model.ExcelOntology import ExcelOntology
from onto_spread_ed.model.Result import Result


class APIService(abc.ABC):
    _config: dict

    def __init__(self, config: dict):
        self._config = config

    @abc.abstractmethod
    def update_api(self, ontology: ExcelOntology, revision_message: str) -> Result[Tuple]:
        ...
