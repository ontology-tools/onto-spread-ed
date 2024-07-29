import abc
import os
from typing import Tuple, Optional

import pyhornedowl
from flask_github import GitHub
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query

from .common import ReleaseCanceledException, local_name, set_release_info, update_release, next_release_step, \
    set_release_result
from ..database.Release import Release
from ..model.ExcelOntology import ExcelOntology
from ..model.Relation import Relation, OWLPropertyType
from ..model.ReleaseScript import ReleaseScript
from ..model.Result import Result
from ..model.Term import Term
from ..services.ConfigurationService import ConfigurationService
from ..utils import download_file


class ReleaseStep(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        ...

    _config: ConfigurationService
    _working_dir: str
    _release_id: int
    _release_script: ReleaseScript
    _gh: GitHub
    _db: SQLAlchemy
    _q: Query[Release]

    _total_items: Optional[int] = None
    _current_item: int = 1

    def __init__(self, db: SQLAlchemy, gh: GitHub, release_script: ReleaseScript, release_id: int, tmp: str,
                 config: ConfigurationService) -> None:
        self._config = config
        self._db = db
        self._gh = gh
        self._release_script = release_script
        self._release_id = release_id
        self._q = db.session.query(Release)
        self._working_dir = tmp

    def _update_progress(self,
                         *,
                         position: Optional[Tuple[int, int]] = None,
                         progress: Optional[float] = None,
                         current_item: Optional[str] = None,
                         message: Optional[str] = None):
        self._set_release_info(dict(__progress=dict(
            position=position,
            progress=progress if progress is not None else (
                (position[0] / position[1]) if position is not None else None),
            current_item=current_item,
            message=message
        )))

    def _next_item(self, *, item: Optional[str] = None, message: Optional[str] = None):
        position = (self._current_item, self._total_items) if self._total_items is not None else None

        self._update_progress(position=position, current_item=item, message=message)

        self._current_item += 1

    @abc.abstractmethod
    def run(self) -> bool:
        ...

    def _raise_if_canceled(self):
        r: Release = self._q.get(self._release_id)
        if r.state == "canceled":
            raise ReleaseCanceledException("Release has been canceled!")

    def _local_name(self, remote_name, file_ending=None) -> str:
        return local_name(self._working_dir, remote_name, file_ending)

    def _set_release_info(self, details) -> None:
        set_release_info(self._q, self._release_id, details)

    def _update_release(self, patch: dict) -> None:
        update_release(self._q, self._release_id, patch)

    def _next_release_step(self) -> None:
        next_release_step(self._q, self._release_id)

    def _set_release_result(self, result):
        set_release_result(self._q, self._release_id, result)

    def _download(self, file: str, local_name: Optional[str] = None):
        if local_name is None:
            local_name = self._local_name(file)

        return download_file(self._gh, self._release_script.full_repository_name, file, local_name)

    def load_externals_ontology(self) -> Result[ExcelOntology]:
        result = Result()

        excel_ontology = ExcelOntology(self._release_script.external.target.iri)
        externals_owl = self._local_name(self._release_script.external.target.file)
        if os.path.exists(externals_owl):
            ontology = pyhornedowl.open_ontology(externals_owl, "rdf")
            for [p, d] in self._config["PREFIXES"]:
                ontology.add_prefix_mapping(p, d)

            for c in ontology.get_classes():
                id = ontology.get_id_for_iri(c)
                labels = ontology.get_annotations(c, self._config['RDFSLABEL'])

                if id is None:
                    result.warning(type='unknown-id', msg=f'Unable to determine id of external term "{c}"')
                if len(labels) == 0:
                    result.warning(type='unknown-label', msg=f'Unable to determine label of external term "{c}"')

                if id is not None:
                    for label in labels:
                        excel_ontology.add_term(Term(
                            id=id,
                            label=label,
                            origin=("<external>", -1),
                            relations=[],
                            sub_class_of=[],
                            equivalent_to=[],
                            disjoint_with=[]
                        ))

            self._raise_if_canceled()

            for r in ontology.get_object_properties():
                id = ontology.get_id_for_iri(r)
                label = ontology.get_annotation(r, self._config['RDFSLABEL'])

                if id is None:
                    result.warning(type='unknown-id', msg=f'Unable to determine id of external relation "{r}"')
                if label is None:
                    result.warning(type='unknown-label', msg=f'Unable to determine label of external relation "{r}"')

                if id is not None and label is not None:
                    excel_ontology.add_relation(Relation(
                        id=id,
                        label=label,
                        origin=("<external>", -1),
                        equivalent_relations=[],
                        inverse_of=[],
                        relations=[],
                        owl_property_type=OWLPropertyType.ObjectProperty,
                        sub_property_of=[],
                        domain=None,
                        range=None
                    ))
        else:
            result.error(type="external-owl-missing",
                         msg="The external OWL file is missing. Ensure it is build before this step")
            return result

        result.value = excel_ontology
        return result
