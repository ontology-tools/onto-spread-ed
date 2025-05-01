import csv
import dataclasses
import itertools
import logging
import os.path
from dataclasses import dataclass, field
from io import BytesIO
from typing import Optional, Union, Iterator, List, Tuple, FrozenSet, Set, Literal, Dict

import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from pyhornedowl import pyhornedowl
from typing_extensions import Self

from .ColumnMapping import ColumnMapping, ColumnMappingKind, LabelMapping, RelationColumnMapping, \
    ParentMapping, TermMapping, PrefixColumnMapping
from .Relation import Relation, UnresolvedRelation, OWLPropertyType
from .Result import Result
from .Schema import Schema, DEFAULT_SCHEMA, DEFAULT_IMPORT_SCHEMA
from .Term import Term, UnresolvedTerm
from .TermIdentifier import TermIdentifier
from .. import constants
from ..utils import str_empty, lower, str_space_eq

# Same as js/common/model.ts
DIAGNOSTIC_KIND = Literal[
    "unknown-column",
    "incomplete-term",
    "unknown-relation",
    "missing-label",
    "missing-label",
    "missing-id",
    "inconsistent-import",
    "missing-import",
    "no-parent",
    "unknown-parent",
    "missing-parent", "ignored-parent",
    "unknown-disjoint",
    "missing-disjoint", "ignored-disjoint",
    "unknown-relation-value",
    "missing-relation-value",
    "ignored-relation-value",
    "unknown-domain",
    "missing-domain",
    "ignored-domain",
    "unknown-range",
    "missing-range",
    "ignored-range",
    "duplicate"
]


@dataclass
class OntologyImport:
    id: str
    iri: Optional[str] = None
    version_iri: Optional[str] = None
    root_id: Optional[TermIdentifier] = None
    imported_terms: List[TermIdentifier] = field(default_factory=list)
    intermediates: Optional[str] = None  # all | minimal
    prefixes: List[(Tuple[str, str])] = field(default_factory=list)
    excluding: List[TermIdentifier] = field(default_factory=list)


class ExcelOntology:
    _logger = logging.getLogger(__name__)
    _terms: List[UnresolvedTerm]
    _relations: List[UnresolvedRelation]
    _imports: List[OntologyImport]
    _used_relations: Set[UnresolvedRelation]
    _discard_status: List[str]
    _ignore_status: List[str]

    def __init__(self, iri: str, version_iri: Optional[str] = None, *,
                 ignore_terms_with_status: Optional[List[str]] = None,
                 discard_terms_with_status: Optional[List[str]] = None):
        """
        Initialises a new instance of an ExcelOntology

        :param str iri: IRI of the ontology
        :param Optional[str] version_iri: An optional IRI indicating the ontology version
        :param Optional[List[str]] ignore_terms_with_status: A list of curation status. If a term's curation status is
                                                            in this list it will be parsed and can be found as possible
                                                            reference target in the resolving step but the term will not
                                                            be added to the list of terms.
        :param Optional[List[str]] discard_terms_with_status: A list of curation status. If a term's curation status is
                                                              in this list it will *NOT* be parsed. This ontology
                                                              instance will never hold terms with this curation status
                                                              internally or externally.
        """

        if ignore_terms_with_status is None:
            ignore_terms_with_status = ['obsolete', 'pre-proposed']
        if discard_terms_with_status is None:
            discard_terms_with_status = []
        self._terms = []
        self._relations = []
        self._imports = []
        self._used_relations = set()

        self._ignore_status = ignore_terms_with_status
        self._discard_status = discard_terms_with_status

        self._iri = iri
        self._version_iri = version_iri

    def imports(self) -> List[OntologyImport]:
        return self._imports.copy()

    def used_relations(self) -> FrozenSet[UnresolvedRelation]:
        return frozenset(self._used_relations)

    def imported_terms(self) -> List[TermIdentifier]:
        return [TermIdentifier(t.id, t.label) for o in self._imports for t in o.imported_terms]

    def terms(self) -> List[Term]:
        return [t.as_resolved() for t in self._terms if not t.is_unresolved() and
                not lower(t.curation_status()) in self._discard_status and lower(
            t.curation_status()) not in self._ignore_status]

    def term_by_label(self, label: str) -> Optional[Term]:
        return next(iter(t for t in (self.terms() + self.imported_terms()) if t.label == label), None)

    def find_term_id(self, label: str) -> Optional[str]:
        return next((t.id for t in (self._terms + self.imported_terms()) if t.label == label), None)

    def find_term_label(self, id: str) -> Optional[str]:
        return next((t.label for t in (self._terms + self.imported_terms()) if t.id == id), None)

    def term_by_id(self, id: str) -> Optional[Union[Term]]:
        return next(iter(t for t in (self.terms()) if t.id == id), None)

    def _term_by_id(self, id: str) -> Optional[Union[UnresolvedTerm]]:
        return next(iter(t for t in self._terms if t.id == id), None)

    def _term_by_label(self, label: str) -> Optional[Union[UnresolvedTerm]]:
        return next(iter(t for t in self._terms if t.label == label), None)

    def _raw_term_by_id(self,
                        id: str,
                        exclude: Optional[UnresolvedTerm] = None) -> Optional[Union[Term, TermIdentifier]]:
        terms_ = [t for t in (self._terms + self.imported_terms()) if t.id == id and (exclude is None or exclude != t)]
        terms_.sort(
            key=lambda t: 1 if isinstance(t, UnresolvedTerm) and lower(
                t.curation_status()) in self._ignore_status else 0)
        return next(iter(terms_), None)

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
            if kind == ColumnMappingKind.IGNORE:
                pass
            elif kind == ColumnMappingKind.ID:
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

        if lower(term.curation_status()) in self._discard_status:
            self._logger.debug(f"Discarding {lower(term.curation_status())} term '{term.label}' ({term.id})'")
        # elif
        # If a term has no id, label, or parents it is probably an empty line.
        # Ignore it but issue a warning.
        elif str_empty(term.id) and str_empty(term.label) and not any(term.sub_class_of):
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
            elif col.get_kind() == ColumnMappingKind.ONTOLOGY_IRI:
                ontology.iri = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.VERSION_IRI:
                ontology.version_iri = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.ROOT_ID and isinstance(col, TermMapping):
                ontology.root_id = col.get_value(val)[0]
            elif col.get_kind() == ColumnMappingKind.EXCLUDED_IMPORT_ID and isinstance(col, TermMapping):
                ontology.excluding += col.get_value(val)
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
                relation.equivalent_relations += col.get_value(val)
            elif kind == ColumnMappingKind.INVERSE_OF:
                relation.inverse_of += col.get_value(val)
            elif isinstance(col, ParentMapping):
                relation.sub_property_of.append(col.get_value(val))
            elif kind == ColumnMappingKind.DOMAIN:
                relation.domain = next(iter(col.get_value(val)), None)
            elif kind == ColumnMappingKind.RANGE:
                relation.range = next(iter(col.get_value(val)), None)
            elif isinstance(col, RelationColumnMapping):
                relation.relations += col.get_value(val)
            elif kind == ColumnMappingKind.RELATION_TYPE:
                relation.owl_property_type = OWLPropertyType[col.get_value(val)]

            elif col not in unprocessable_columns:
                r.warning(column=col.get_name(),
                          type="unprocessable-column",
                          msg=f"The column '{col.get_name()}' could not be processed")
                unprocessable_columns.append(col)

        r.value = relation
        return r

    def add_term(self, term: Term):
        self._used_relations = set.union(self._used_relations,
                                         {UnresolvedRelation(r.id, r.label) for r, _ in term.relations})
        self._terms.append(UnresolvedTerm(**term.__dict__))

    def add_imported_terms(self, name: str, file: Union[bytes, str, BytesIO],
                           schema: Optional[Schema] = None) -> Result[tuple]:
        if schema is None:
            schema = DEFAULT_IMPORT_SCHEMA

        result = self._open_excel(name, file, schema)
        data, mapped = result.value

        result += Result((), template=dict(file=name))
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
        result = self._open_excel(name, file, schema)
        data, mapped = result.value

        result += Result((), template=dict(file=name))
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

    def merge(self, other: Self) -> None:
        self._terms += other._terms
        self._used_relations = set.union(self._used_relations, other._used_relations)
        self._imports += other._imports
        self._relations += other._relations

    def add_terms_from_excel(self, name: str, file: Union[bytes, str, BytesIO],
                             schema: Optional[Schema] = None) -> Result[tuple]:
        result = self._open_excel(name, file, schema)
        data, mapped = result.value

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(UnresolvedRelation(**c.relation.__dict__))

        result += Result((), template=dict(file=name))
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
        result = self._open_excel(name, file, schema)
        data, mapped = result.value

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(UnresolvedRelation(**c.relation.__dict__))

        result += Result((), template=dict(file=name))
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

    def apply_new_parents(self, file: str) -> None:
        with open(file, "r") as f:
            rows = csv.reader(f)
            next(rows)

            for row in rows:
                # Skip potential ROBOT header
                if row[0] == "ID" or len(row) < 3:
                    continue

                id = row[0]
                new_parent = row[1]

                term = self._term_by_id(id)

                if term is not None:
                    term.sub_class_of.append(TermIdentifier(new_parent))

    def apply_renamings(self, file: str, scope: Literal['self', 'import', 'all'] = 'all') -> None:
        with open(file, "r") as f:
            rows = csv.reader(f)
            next(rows)

            for row in rows:
                # Skip potential ROBOT header
                if row[0] == "ID" or len(row) < 2:
                    continue

                id = row[0]
                label = row[1]

                if scope == 'self' or scope == 'all':
                    term = self._term_by_id(id)

                    if term is not None:
                        term.label = label

                if scope == 'import' or scope == 'all':
                    term = next((t for i in self._imports for t in i.imported_terms if t.id == id), None)

                    if term is not None:
                        term.label = label

    def _open_excel(self, origin: str, file: Union[bytes, str, BytesIO], schema: Optional[Schema] = None) -> \
            Result[Tuple[Iterator[Iterator[Optional[str]]], List[ColumnMapping]]]:
        result = Result()
        if schema is None:
            schema = DEFAULT_SCHEMA
        if isinstance(file, bytes):
            file = BytesIO(file)
        wb = openpyxl.load_workbook(file)
        sheet: Worksheet = wb.active
        data = sheet.rows
        header = next(data)
        mapped: List[ColumnMapping] = []
        for h in header:
            if h.value is None:
                continue

            header_name = h.value.strip()
            mapping = schema.get_mapping(origin, header_name)
            if mapping is None and not schema.is_ignored(header_name):
                result.warning(type='unknown-column',
                               column=header_name,
                               sheet=os.path.basename(file) if isinstance(file, str) else sheet.title)

            mapped.append(mapping)

        result.value = (data, mapped)
        return result

    def resolve(self) -> Result[tuple]:
        result = Result(())
        imported = self.imported_terms()

        for term in self._terms:
            if lower(term.curation_status()) in self._ignore_status + self._discard_status:
                self._logger.debug(f"Not resolving {term.curation_status()} term {term.label} ({term.id})")
                continue

            if term.id is None or term.label is None:
                self._logger.error(f"Term without id or label encountered. This should not happen. Term: {term}")
                # continue

            if term.is_resolved():
                continue

            relation_values = [x for r, x in term.relations if isinstance(x, TermIdentifier)]
            unresolved: List[TermIdentifier] = ([*term.sub_class_of, *term.disjoint_with] +
                                                relation_values)
            unresolved = [i for i in unresolved if i.is_unresolved()]
            for unresolved_term in unresolved:
                matching_terms = [t for t in (self._terms + imported) if t != unresolved_term and
                                  (unresolved_term.label is not None and unresolved_term.label == t.label or
                                   unresolved_term.id is not None and unresolved_term.id == t.id)]

                matching_terms.sort(key=lambda t: 1 if isinstance(t, UnresolvedTerm) and (
                        lower(t.curation_status()) in self._ignore_status) else 0)

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
                    if isinstance(m, UnresolvedTerm) and \
                            lower(m.curation_status()) in self._ignore_status + self._discard_status:
                        continue

                    relation.range.complement(m)

            if relation.domain and relation.domain.is_unresolved():
                matching_terms = [t for t in (self._terms + imported) if
                                  (relation.domain.label is not None and relation.domain.label == t.label or
                                   relation.domain.id is not None and relation.domain.id == t.id)]

                for m in matching_terms:
                    if isinstance(m, UnresolvedTerm) and \
                            lower(m.curation_status()) in self._ignore_status + self._discard_status:
                        continue

                    relation.domain.complement(m)

            for sub in relation.sub_property_of:
                matching_terms = [t for t in (self._terms + imported) if
                                  (sub.label is not None and sub.label == t.label or
                                   sub.id is not None and sub.id == t.id)]

                for m in matching_terms:
                    if isinstance(m, UnresolvedTerm) and \
                            lower(m.curation_status()) in self._ignore_status + self._discard_status:
                        continue

                    sub.complement(m)

            for er in relation.equivalent_relations:
                matching_terms = [t for t in (self._terms + imported) if
                                  (er.label is not None and er.label == t.label or
                                   er.id is not None and er.id == t.id)]

                for m in matching_terms:
                    if isinstance(m, UnresolvedTerm) and \
                            lower(m.curation_status()) in self._ignore_status + self._discard_status:
                        continue

                    er.complement(m)

        replacements: List[Tuple[UnresolvedRelation, UnresolvedRelation]] = []
        for relation in self._used_relations:
            if relation.is_unresolved():
                matching = next((r for r in self._relations if not r.is_unresolved() and (
                        r.label == relation.label or r.id == id)), None)

                if matching is not None:
                    replacements.append((relation, matching))
                    continue

                matching = next((t for i in self._imports for t in i.imported_terms if
                                 t.id == relation.id or t.label == relation.label), None)
                if matching is not None:
                    relation.id = matching.id
                    relation.label = matching.label

        for old, new in replacements:
            self._used_relations.remove(old)
            self._used_relations.add(new)

        for term in self._terms:
            for relation, _ in term.relations:
                if relation.is_unresolved():
                    used_relations = [r for r in self._used_relations if
                                      (r.label is None or relation.label is None or relation.label == r.label) and
                                      (r.id is None or relation.label is None or relation.label == r.label)]
                    for r in used_relations:
                        relation.complement(r.identifier())

        return result

    def validate(self,
                 only: Optional[List[DIAGNOSTIC_KIND]] = None,
                 exclude: Optional[List[DIAGNOSTIC_KIND]] = None) -> Result[tuple]:
        """
        Validate the loaded ontology. Checks for various errors such as unknown parents, related terms, duplicates, etc.

        :param only: List of errors or warning to report. If ``None``, all errors are reported
                     (if not excluded by `exclude`)
        :param exclude: List of errors to exclude. If ``None``, no errors are explicitly excluded.
        """
        result = Result()

        def c(arg1: DIAGNOSTIC_KIND, arg2: Optional[DIAGNOSTIC_KIND] = None) -> bool:
            """
            Helper function to check if specific errors or warnings should be flagged
            """
            args = [a for a in [arg1, arg2] if a is not None]
            return (only is None or any(a in only for a in args)) and \
                (exclude is None or not all(a in exclude for a in args))

        imported_terms = set(t for i in self._imports for t in i.imported_terms)

        # To find duplicates store a list of terms with the same ID or label
        by_id: Dict[str, List[Union[UnresolvedTerm, UnresolvedRelation]]] = {}
        by_label: Dict[str, List[Union[UnresolvedTerm, UnresolvedRelation]]] = {}

        for term in self._terms:
            result.template = {"row": term.origin[1], "origin": term.origin[0]} if term.origin is not None else {}
            if lower(term.curation_status()) in self._ignore_status + self._discard_status:
                self._logger.debug(f"Not validating {term.curation_status()} term {term.label} ({term.id})")
                continue

            if c("missing-label") and term.label is None:
                result.error(type="missing-label",
                             term=term.__dict__)

            if c("missing-id") and term.id is None:
                result.error(type="missing-id",
                             term=term.__dict__)

            by_id.setdefault(term.id, []).append(term)
            by_label.setdefault(term.label, []).append(term)

            if (c("inconsistent-import", "missing-import") and
                    lower(term.curation_status()) == 'external' and term.identifier() not in imported_terms):
                imported_term = next((t for t in imported_terms if t.id == term.id or t.label == term.label), None)
                if imported_term is not None:
                    if c("inconsistent-import"):
                        result.warning(type="inconsistent-import",
                                       imported_term=imported_term,
                                       term=term.__dict__)
                elif c("missing-import"):
                    result.warning(type="missing-import",
                                   term=term.__dict__)

            if c("no-parent") and len(term.sub_class_of) < 1:
                result.error(type="no-parent",
                             term=term.__dict__)

            for p in term.sub_class_of:
                if c("unknown-parent") and p.is_unresolved():
                    result.error(type="unknown-parent",
                                 term=term.__dict__,
                                 parent=p.__dict__)
                elif c("missing-parent", "ignored-parent"):
                    t = self._raw_term_by_id(p.id)
                    if c("missing-parent") and t is None:
                        result.error(type="missing-parent",
                                     term=term.__dict__,
                                     parent=p.__dict__)
                    elif c("ignored-parent") and isinstance(t, UnresolvedTerm) and lower(
                            t.curation_status()) in self._ignore_status:
                        result.error(type="ignored-parent",
                                     status=t.curation_status(),
                                     term=term.__dict__,
                                     parent=p.__dict__)

            for p in term.disjoint_with:
                if c("unknown-disjoint") and p.is_unresolved():
                    result.error(type="unknown-disjoint",
                                 term=term.__dict__,
                                 disjoint_class=p.__dict__)
                elif c("missing-disjoint", "ignored-disjoint"):
                    t = self._raw_term_by_id(p.id)
                    if c("missing-disjoint") and t is None:
                        result.error(type="missing-disjoint",
                                     term=term.__dict__,
                                     disjoint_class=p.__dict__)
                    elif c("ignored-disjoint") and isinstance(t, UnresolvedTerm) and lower(
                            t.curation_status()) in self._ignore_status:
                        result.error(type="ignored-disjoint",
                                     status=t.curation_status(),
                                     term=term.__dict__,
                                     disjoint_class=p.__dict__)

            for relation, value in term.relations:
                if isinstance(value, TermIdentifier):
                    if c("unknown-relation-value") and value.is_unresolved():
                        result.error(type="unknown-relation-value",
                                     relation=relation,
                                     value=value,
                                     term=term.__dict__)
                    else:
                        t = self._raw_term_by_id(value.id)
                        if c("missing-relation-value") and t is None:
                            result.error(type="missing-relation-value",
                                         term=term.__dict__,
                                         relation=relation,
                                         value=value)
                        elif c("ignored-relation-value") and isinstance(t, UnresolvedTerm) and lower(
                                t.curation_status()) in self._ignore_status:
                            result.error(type="ignored-relation-value",
                                         status=t.curation_status(),
                                         term=term.__dict__,
                                         relation=relation,
                                         value=value)

        for relation in self._relations:
            result.template = {"row": relation.origin[1]} if relation.origin is not None else {}
            if c("missing-label") and relation.label is None:
                result.error(type="missing-label",
                             relation=relation.__dict__)

            if c("missing-id") and relation.id is None:
                result.error(type="missing-id",
                             relation=relation.__dict__)

            by_id.setdefault(relation.id, []).append(relation)
            by_label.setdefault(relation.label, []).append(relation)

            if relation.domain:
                if c("unknown-domain") and relation.domain.is_unresolved():
                    result.error(type="unknown-domain",
                                 relation=relation.__dict__)
                else:
                    t = self._raw_term_by_id(relation.domain.id)
                    if c("missing-domain") and t is None:
                        result.error(type="missing-domain",
                                     relation=relation.__dict__,
                                     domain=relation.domain.__dict__)
                    elif c("ignored-domain") and isinstance(t, UnresolvedTerm) and lower(
                            t.curation_status()) in self._ignore_status:
                        result.error(type="ignored-domain",
                                     status=t.curation_status(),
                                     relation=relation.__dict__,
                                     domain=relation.domain.__dict__)

            if relation.range:
                if c("unknown-range") and relation.range.is_unresolved():
                    result.error(type="unknown-range",
                                 relation=relation.__dict__)
                else:
                    t = self._raw_term_by_id(relation.range.id)
                    if c("missing-range") and t is None:
                        result.error(type="missing-range",
                                     relation=relation.__dict__,
                                     range=relation.range.__dict__)
                    elif c("ignored-range") and isinstance(t, UnresolvedTerm) and lower(
                            t.curation_status()) in self._ignore_status:
                        result.error(type="ignored-range",
                                     status=t.curation_status(),
                                     relation=relation.__dict__,
                                     range=relation.range.__dict__)

            for p in relation.sub_property_of:
                if c("unknown-parent") and p.is_unresolved():
                    result.error(type="unknown-parent",
                                 term=relation.__dict__,
                                 parent=p.__dict__)
                else:
                    t = self._raw_term_by_id(p.id)
                    if c("missing-parent") and t is None:
                        result.error(type="missing-parent",
                                     term=relation.__dict__,
                                     parent=p.__dict__)
                    elif c("ignored-parent") and isinstance(t, UnresolvedTerm) and lower(
                            t.curation_status()) in self._ignore_status:
                        result.error(type="ignored-parent",
                                     status=t.curation_status(),
                                     term=relation.__dict__,
                                     parent=p.__dict__)

            for r, value in relation.relations:
                if isinstance(value, TermIdentifier):
                    if c("unknown-relation-value") and value.is_unresolved():
                        result.error(type="unknown-relation-value",
                                     relation=r,
                                     value=value,
                                     term=relation.__dict__)
                    else:
                        t = self._raw_term_by_id(value.id)
                        if c("missing-relation-value") and t is None:
                            result.error(type="missing-relation-value",
                                         term=relation.__dict__,
                                         relation=r,
                                         value=value)
                        elif c("ignored-relation-value") and isinstance(t, UnresolvedTerm) and lower(
                                t.curation_status()) in self._ignore_status:
                            result.error(type="ignored-relation-value",
                                         status=t.curation_status(),
                                         term=relation.__dict__,
                                         relation=r,
                                         value=value)

        # Check that all relations used in the spreadsheets (column headers) are defined
        for relation in self._used_relations:
            if relation.owl_property_type == OWLPropertyType.Internal:
                continue

            result.template = {"row": relation.origin[1]} if relation.origin is not None else {}
            if relation.is_unresolved():
                result.error(type="unknown-relation",
                             relation=relation.__dict__)

        # Check for duplicates
        if c("duplicate"):
            for k, items in itertools.chain(by_id.items(), by_label.items()):
                duplicates = [d for d in items
                              if not isinstance(d, UnresolvedTerm) or d.curation_status() not in self._ignore_status]
                if len(duplicates) > 1:
                    mismatches = []
                    for a, b in itertools.combinations(duplicates, 2):
                        if a.id is None or b.id is None or a.label is None or b.label is None:
                            continue
                        if a.label != b.label:
                            mismatches.append(("label", a, b))
                        if a.id != b.id:
                            mismatches.append(("id", a, b))
                        if isinstance(a, UnresolvedTerm) and isinstance(b, UnresolvedTerm):
                            definition_a = (a.definition()
                                            .replace("<", "")
                                            .replace(">", "")) if a.definition() is not None else ""
                            definition_b = (b.definition()
                                            .replace("<", "")
                                            .replace(">", "")) if b.definition() is not None else ""
                            if not str_space_eq(definition_a, definition_b):
                                mismatches.append(("definition", a, b))
                            if not str_space_eq(a.curation_status(), b.curation_status()):
                                mismatches.append(("curation status", a, b))
                        elif isinstance(a, UnresolvedRelation) and isinstance(b, UnresolvedRelation):
                            pass
                        else:
                            mismatches.append(("type", a, b))
                    if len(mismatches) > 0:
                        result.error(type="duplicate",
                                     duplicate_field="id" if k in by_id else "label",
                                     duplicate_value=k,
                                     duplicates=list(set(x for _, a, b in mismatches for x in [a, b])),
                                     mismatches=[dict(field=f, a=a, b=b) for f, a, b in mismatches])

        if not any(result.errors):
            result.value = ()

        return result

    def remove_duplicates(self) -> int:
        to_remove: List[UnresolvedTerm] = []
        hashset: Set[TermIdentifier] = set()
        for term in self._terms:
            if term.identifier() in hashset:
                to_remove.append(term)
            else:
                hashset.add(term.identifier())

        for term in to_remove:
            self._terms.remove(term)

        return len(to_remove)

    def iri(self) -> str:
        return self._iri

    def add_relation(self, relation: Relation):
        self._relations.append(UnresolvedRelation(**dataclasses.asdict(relation)))

    @classmethod
    def from_excel(cls, iri: str, files: Tuple[str, Union[bytes, str, BytesIO], Literal["classes", "relations"]]):
        ontology = ExcelOntology(iri)
        for name, file, kind in files:
            if kind == "classes":
                ontology.add_terms_from_excel(name, file)
            elif kind == "relations":
                ontology.add_relations_from_excel(name, file)

        return ontology

    @classmethod
    def from_owl(cls, externals_owl: str, prefixes: Dict[str, str]) -> Result[Self]:
        result = Result()
        ontology = pyhornedowl.open_ontology(externals_owl, "owx")
        self = ExcelOntology(ontology.get_iri())
        for (p, d) in prefixes.items():
            ontology.prefix_mapping.add_prefix(p, d)

        for c in ontology.get_classes():
            id = ontology.get_id_for_iri(c)
            labels = ontology.get_annotations(c, constants.RDFS_LABEL)

            if id is None:
                result.warning(type='unknown-id', msg=f'Unable to determine id of external term "{c}"')
            if len(labels) == 0:
                result.warning(type='unknown-label', msg=f'Unable to determine label of external term "{c}"')

            if id is not None:
                for label in labels:
                    self.add_term(Term(
                        id=id,
                        label=label,
                        origin=("<external>", -1),
                        relations=[],
                        sub_class_of=[],
                        equivalent_to=[],
                        disjoint_with=[]
                    ))

        for r in ontology.get_object_properties():
            id = ontology.get_id_for_iri(r)
            label = ontology.get_annotation(r, constants.RDFS_LABEL)

            if id is None:
                result.warning(type='unknown-id', msg=f'Unable to determine id of external relation "{r}"')
            if label is None:
                result.warning(type='unknown-label', msg=f'Unable to determine label of external relation "{r}"')

            if id is not None and label is not None:
                self.add_relation(Relation(
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

        result.value = self
        return result

    def to_excel(self, include_origin: bool = False) -> Workbook:
        relations = self.used_relations()

        wb = Workbook()
        ws: Worksheet = wb.active

        header = ["ID", "Label", "Parent", "Disjoint classes", "Logical definition"] + [
            (r.label if r.id is None else f"REL '{r.label}'") for r in relations]
        if include_origin:
            header += ["origin"]

        ws.append(header)

        for term in self._terms:
            row = [term.id, term.label,
                   "; ".join(f"{s.label} [{s.id}]" if s.id else s.label for s in term.sub_class_of),
                   "; ".join(f"{s.label} [{s.id}]" if s.id else s.label for s in term.disjoint_with),
                   "; ".join(term.equivalent_to),
                   ] + [term.get_relation_value(r.identifier()) for r in relations]

            if include_origin:
                row += [":".join(term.origin)]

            ws.append(row)

        return wb
