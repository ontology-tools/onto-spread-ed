import abc

from onto_spread_ed.model.ExcelOntology import ExcelOntology


class APIService(abc.ABC):
    _config: dict

    def __init__(self, config: dict):
        self._config = config

    @abc.abstractmethod
    def update_api(self, ontology: ExcelOntology, revision_message: str):
        ...
