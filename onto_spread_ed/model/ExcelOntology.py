import logging
from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional, Union, Iterator, List, Tuple, FrozenSet, Set

import openpyxl
from typing_extensions import Self

from .ColumnMapping import Schema, ColumnMapping, ColumnMappingKind, LabelMapping, RelationColumnMapping, \
    ParentMapping, DEFAULT_MAPPINGS, DEFAULT_IMPORT_SCHEMA, TermMapping, PrefixColumnMapping
from .Relation import Relation, UnresolvedRelation, OWLPropertyType
from .Result import Result
from .Term import Term, UnresolvedTerm
from .TermIdentifier import TermIdentifier
from ..utils import str_empty


@dataclass
class OntologyImport:
    id: str
    purl: Optional[str] = None
    root_id: Optional[TermIdentifier] = None
    imported_terms: List[TermIdentifier] = field(default_factory=list)
    intermediates: Optional[str] = None  # all | minimal
    prefixes: List[(Tuple[str, str])] = field(default_factory=list)


class ExcelOntology:
    _logger = logging.getLogger(__name__)
    _terms: List[UnresolvedTerm]
    _relations: List[UnresolvedRelation]
    _imports: List[OntologyImport]
    _used_relations: Set[Relation]

    def __init__(self, iri: str, version_iri: Optional[str] = None):
        self._terms = []
        self._relations = []
        self._imports = []
        self._used_relations = set()

        self._iri = iri
        self._version_iri = version_iri

    def imports(self) -> List[OntologyImport]:
        return self._imports.copy()

    def used_relations(self) -> FrozenSet[Relation]:
        return frozenset(self._used_relations)

    def imported_terms(self) -> List[TermIdentifier]:
        return [TermIdentifier(t.id, t.label) for o in self._imports for t in o.imported_terms]

    def terms(self) -> List[Term]:
        return [t.as_resolved() for t in self._terms if not t.is_unresolved()]

    def term_by_label(self, label: str) -> Optional[Term]:
        return next(iter(t for t in (self.terms() + self.imported_terms()) if t.label == label), None)

    def find_term_id(self, label: str) -> Optional[str]:
        return next((t.id for t in (self._terms + self.imported_terms()) if t.label == label), None)

    def find_term_label(self, id: str) -> Optional[str]:
        return next((t.label for t in (self._terms + self.imported_terms()) if t.id == id), None)

    def term_by_id(self, id: str) -> Optional[Term]:
        return next(iter(t for t in (self.terms() + self.imported_terms()) if t.id == id), None)

    def _unresolved_term_by_label(self, label: str, exclude: Optional[UnresolvedTerm] = None) -> List[UnresolvedTerm]:
        return list(t for t in self._terms if t.label == label and (exclude is None or exclude != t))

    def _unresolved_term_by_id(self, id: str, exclude: Optional[UnresolvedTerm] = None) -> List[UnresolvedTerm]:
        return list(t for t in self._terms if t.id == id and (exclude is None or exclude != t))

    def relations(self) -> List[Relation]:
        return [r.as_resolved() for r in self._relations if not r.is_unresolved()]

    def _parse_term(self, row: List[Tuple[ColumnMapping, Optional[str]]], err_default: dict) -> Result[UnresolvedTerm]:
        r = Result(template=err_default)
        term = UnresolvedTerm()
        unprocessable_columns = []
        for col, val in row:
            if val is None:
                continue

            if not col.valid(val):
                r.error(column=col.get_name(),
                        type="invalid-value",
                        msg=f"Invalid value '{val}'")
                continue

            kind = col.get_kind()
            if kind == ColumnMappingKind.ID:
                term.id = col.get_value(val)
            elif kind == ColumnMappingKind.DISJOINT_WITH:
                term.disjoint_with += col.get_value(val)
            elif kind == ColumnMappingKind.EQUIVALENT_TO:
                term.equivalent_to.append(col.get_value(val))
            elif isinstance(col, LabelMapping):
                term.label = col.get_label(val)
            elif isinstance(col, RelationColumnMapping):
                term.relations += col.get_value(val)
            # TODO: SYNONYMS field
            elif isinstance(col, ParentMapping):
                term.sub_class_of.append(col.get_value(val))

            elif col not in unprocessable_columns:
                r.warning(column=col.get_name(),
                          type="unprocessable-column",
                          msg=f"The column '{col.get_name()}' could not be processed")
                unprocessable_columns.append(col)

        # If a term has no id, label, or parents it is probably an empty line.
        # Ignore it but issue a warning.
        if str_empty(term.id) and str_empty(term.label) and not any(term.sub_class_of):
            r.warning(type="incomplete-term",
                      msg="Empty or incomplete term")
        else:
            r.value = term

        return r

    def _parse_import(self,
                      row: List[Tuple[ColumnMapping, Optional[str]]],
                      err_default: dict) -> Result[OntologyImport]:
        r = Result(template=err_default)
        ontology = OntologyImport(id=None)
        unprocessable_columns = []
        for col, val in row:
            if val is None:
                continue

            if not col.valid(val):
                r.error(column=col.get_name(),
                        type="invalid-value",
                        msg=f"Invalid value '{val}'")
                continue

            if col.get_kind() == ColumnMappingKind.ONTOLOGY_ID:
                ontology.id = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.PURL:
                ontology.purl = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.ROOT_ID and isinstance(col, TermMapping):
                ontology.root_id = col.get_value(val)[0]
            elif col.get_kind() == ColumnMappingKind.IMPORTED_ID and isinstance(col, TermMapping):
                ontology.imported_terms = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.PLAIN and col.get_name().lower() == "intermediates":
                ontology.intermediates = col.get_value(val)
            elif isinstance(col, PrefixColumnMapping):
                ontology.prefixes = col.get_value(val)
            elif col not in unprocessable_columns:
                r.warning(column=col.get_name(),
                          type="unprocessable-column",
                          msg=f"The column '{col.get_name()}' could not be processed")
                unprocessable_columns.append(col)

        r.value = ontology
        return r

    def _parse_relation(self,
                        row: List[Tuple[ColumnMapping, Optional[str]]],
                        err_default: dict) -> Result[UnresolvedRelation]:
        r = Result(template=err_default)
        relation = UnresolvedRelation(owl_property_type=OWLPropertyType.ObjectProperty)
        unprocessable_columns = []
        for col, val in row:
            if val is None:
                continue

            if not col.valid(val):
                r.error(column=col.get_name(),
                        type="invalid-value",
                        msg=f"Invalid value '{val}'")
                continue

            kind = col.get_kind()
            if kind == ColumnMappingKind.ID:
                relation.id = col.get_value(val)
            elif isinstance(col, LabelMapping):
                relation.label = col.get_value(val)
            elif kind == ColumnMappingKind.EQUIVALENT_TO:
                relation.synonyms.append(col.get_value(val))
            elif isinstance(col, ParentMapping):
                relation.sub_property_of.append(col.get_value(val))
            elif kind == ColumnMappingKind.DOMAIN:
                relation.domain = TermIdentifier(label=col.get_value(val))
            elif kind == ColumnMappingKind.RANGE:
                relation.range = TermIdentifier(label=col.get_value(val))
            elif isinstance(col, RelationColumnMapping):
                relation.relations += col.get_value(val)

            elif col not in unprocessable_columns:
                r.warning(column=col.get_name(),
                          type="unprocessable-column",
                          msg=f"The column '{col.get_name()}' could not be processed")
                unprocessable_columns.append(col)

        r.value = relation
        return r

    def add_imported_terms(self, name: str, file: Union[bytes, str, BytesIO],
                           schema: Optional[Schema] = None) -> Result[tuple]:
        if schema is None:
            schema = DEFAULT_IMPORT_SCHEMA

        data, mapped = self._open_excel(file, schema)

        result = Result((), template=dict(file=name))
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            result = result.merge(
                self._parse_import([(m, c.value) for m, c in zip(mapped, row) if m is not None],
                                   dict(row=row_idx, origin=origin)))

            if result.ok():
                term = result.value
                term.origin = (name, row_idx)
                self._imports.append(term)

        return result.merge(Result(()))

    def import_other_excel_ontology(self, other: Self) -> Result[tuple]:
        result = Result((), template=dict(file=other._iri))
        imported_terms = []
        for term in other._terms + other._relations:
            if not term.identifier().is_unresolved():
                imported_terms.append(term.identifier())

        ontology = OntologyImport(id=other._iri, imported_terms=[t for t in imported_terms])
        self._imports.append(ontology)

        return result

    def import_excel_ontology_from_file(self, name: str, file: Union[bytes, str, BytesIO],
                                        schema: Optional[Schema] = None) -> Result[tuple]:
        imported_terms = []
        data, mapped = self._open_excel(file, schema)

        result = Result((), template=dict(file=name))
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            result = result.merge(
                self._parse_term([(m, c.value) for m, c in zip(mapped, row) if m is not None],
                                 dict(row=row_idx, origin=origin)))

            if result.ok():
                term = result.value
                term.origin = origin
                imported_terms.append(term.identifier())

        ontology = OntologyImport(id=name, imported_terms=[t for t in imported_terms])
        self._imports.append(ontology)

        return result.merge(Result(()))

    def add_terms_from_excel(self, name: str, file: Union[bytes, str, BytesIO],
                             schema: Optional[Schema] = None) -> Result[tuple]:
        data, mapped = self._open_excel(file, schema)

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(c.relation)

        result = Result((), template=dict(file=name))
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            result = result.merge(
                self._parse_term([(m, c.value) for m, c in zip(mapped, row) if m is not None],
                                 dict(row=row_idx, origin=origin)))

            if result.ok():
                term = result.value
                term.origin = origin
                self._terms.append(term)

        return result.merge(Result(()))

    def add_relations_from_excel(self, name: str, file: Union[bytes, str, BytesIO],
                                 schema: Optional[Schema] = None) -> Result[tuple]:
        data, mapped = self._open_excel(file, schema)

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(c.relation)

        result = Result((), template=dict(file=name))
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            result = result.merge(
                self._parse_relation([(m, c.value) for m, c in zip(mapped, row) if m is not None],
                                     dict(row=row_idx, origin=origin)))

            if result.ok():
                relation = result.value
                relation.origin = (name, row_idx)

                self._relations.append(relation)

        return result.merge(Result(()))

    def _open_excel(self, file: Union[bytes, str, BytesIO], schema: Optional[Schema] = None) -> \
            Tuple[Iterator[Iterator[Optional[str]]], List[ColumnMapping]]:
        if schema is None:
            schema = Schema(DEFAULT_MAPPINGS)
        if isinstance(file, bytes):
            file = BytesIO(file)
        wb = openpyxl.load_workbook(file)
        sheet = wb.active
        data = sheet.rows
        header = next(data)
        mapped = [schema.get_mapping(h.value) for h in header if h.value is not None]
        return data, mapped

    def resolve(self) -> Result[tuple]:
        result = Result(())
        imported = self.imported_terms()

        for term in self._terms:
            if not term.is_unresolved():
                continue

            if term.id is None and term.label is None:
                self._logger.error(f"Term without id and label encountered. This should not happen. Term: {term}")
                continue

            matching_terms = [t for t in self._terms if t != term and
                              (term.label is not None and term.label == t.label or
                               term.id is not None and term.id == t.id)]

            for m in matching_terms:
                term.complement(m)

            if term.is_unresolved():
                matching_import = next((t for t in imported if
                                        (term.label is not None and term.label == t.label or
                                         term.id is not None and term.id == t.id)), None)
                if matching_import is not None:
                    term.complement(matching_import)

        for term in self._terms:
            if not term.is_unresolved():
                continue

            relation_values = [x for r, x in term.relations if isinstance(x, TermIdentifier)]
            unresolved: List[TermIdentifier] = ([*term.sub_class_of, *term.disjoint_with] +
                                                relation_values)
            unresolved = [i for i in unresolved if i.is_unresolved()]
            for unresolved_term in unresolved:
                matching_terms = [t for t in (self._terms + imported) if t != unresolved_term and
                                  (unresolved_term.label is not None and unresolved_term.label == t.label or
                                   unresolved_term.id is not None and unresolved_term.id == t.id)]

                for m in matching_terms:
                    unresolved_term.complement(m)

        for relation in self._relations:
            if not relation.is_unresolved():
                continue

            matching_import = next((t for t in imported if
                                    (relation.label is not None and relation.label == t.label or
                                     relation.id is not None and relation.id == t.id)), None)

            if matching_import is not None:
                if matching_import.id is not None:
                    relation.id = matching_import.id
                if matching_import.label is not None:
                    relation.label = matching_import.label

            if relation.range and relation.range.is_unresolved():
                matching_terms = [t for t in (self._terms + imported) if
                                  (relation.range.label is not None and relation.range.label == t.label or
                                   relation.range.id is not None and relation.range.id == t.id)]

                for m in matching_terms:
                    relation.range.complement(m)

            if relation.domain and relation.domain.is_unresolved():
                matching_terms = [t for t in (self._terms + imported) if
                                  (relation.domain.label is not None and relation.domain.label == t.label or
                                   relation.domain.id is not None and relation.domain.id == t.id)]

                for m in matching_terms:
                    relation.domain.complement(m)

            for sub in relation.sub_property_of:
                matching_terms = [t for t in (self._terms + imported) if
                                  (sub.label is not None and sub.label == t.label or
                                   sub.id is not None and sub.id == t.id)]

                for m in matching_terms:
                    sub.complement(m)

        return result

    def validate(self) -> Result[tuple]:
        result = Result()

        for term in self._terms:
            result.template = {"row": term.origin[1]} if term.origin is not None else {}
            # if term.is_unresolved():
            if term.label is None:
                result.error(type="missing-label",
                             term=term.__dict__)

            if term.id is None:
                result.error(type="unknown-label",
                             term=term.__dict__)

            for p in term.sub_class_of:
                if p.is_unresolved():
                    result.error(type="unknown-parent",
                                 term=term.__dict__,
                                 parent=p.__dict__)
                elif self.term_by_id(p.id) is None:
                    result.error(type="missing-parent",
                                 term=term.__dict__,
                                 parent=p.__dict__)

            for p in term.disjoint_with:
                if p.is_unresolved():
                    result.error(type="unknown-disjoint",
                                 term=term.__dict__,
                                 disjoint_class=p.__dict__)
                elif self.term_by_id(p.id) is None:
                    result.error(type="missing-disjoint",
                                 term=term.__dict__,
                                 disjoint_class=p.__dict__)

            for relation, value in term.relations:
                if isinstance(value, TermIdentifier):
                    if value.is_unresolved():
                        result.error(type="unknown-relation-value",
                                     relation=relation,
                                     value=value,
                                     term=term.__dict__)
                    elif self.term_by_id(value.id) is None:
                        result.error(type="missing-relation-value",
                                     term=term.__dict__,
                                     relation=relation,
                                     value=value)

        for relation in self._relations:
            result.template = {"row": relation.origin[1]} if relation.origin is not None else {}
            if relation.is_unresolved():
                if relation.label is None:
                    result.error(type="missing-label",
                                 relation=relation.__dict__)

                if relation.id is None:
                    result.error(type="unknown-label",
                                 relation=relation.__dict__)

                if relation.domain and relation.domain.is_unresolved():
                    result.error(type="unknown-domain",
                                 relation=relation.__dict__)

                if relation.range and relation.range.is_unresolved():
                    result.error(type="unknown-range",
                                 relation=relation.__dict__)

                for p in relation.sub_property_of:
                    if p.is_unresolved():
                        result.error(type="unknown-parent",
                                     relation=relation.__dict__,
                                     parent=p.__dict__)

        if not any(result.errors):
            result.value = ()

        return result

    def iri(self) -> str:
        return self._iri
