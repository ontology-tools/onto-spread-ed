from collections import defaultdict
import csv
import dataclasses
import itertools
import logging
import os.path
import zipfile
from io import BytesIO
from typing import (
    DefaultDict,
    Optional,
    Union,
    Iterator,
    List,
    Tuple,
    FrozenSet,
    Set,
    Literal,
    Dict,
)

import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
import pyhornedowl as ho
from typing_extensions import Self

from ose.schema import (
    ColumnMapping,
    ColumnMappingKind,
    LabelMapping,
    RelationColumnMapping,
    ParentMapping,
    TermMapping,
    PrefixColumnMapping,
    Schema,
    DEFAULT_SCHEMA,
    DEFAULT_IMPORT_SCHEMA,
    TermBase,
    Term,
    UnresolvedTerm,
    TermIdentifierBase,
    TermIdentifier,
    termid,
    Relation,
    UnresolvedRelation,
    OWLPropertyType,
)
from ose.result import ResultContext, with_result_context_method, is_successful
from ose import constants
from ose.utils import str_empty, lower, str_space_eq

from pydantic import BaseModel

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
    "missing-parent",
    "ignored-parent",
    "unknown-disjoint",
    "missing-disjoint",
    "ignored-disjoint",
    "unknown-relation-value",
    "missing-relation-value",
    "ignored-relation-value",
    "unknown-domain",
    "missing-domain",
    "ignored-domain",
    "unknown-range",
    "missing-range",
    "ignored-range",
    "duplicate",
]


def get_id(ontology: ho.PyIndexedOntology, iri: str):
    id = ontology.get_id_for_iri(iri)

    # Check if it uses a PURL IRI
    if id is None and iri.startswith("http://purl.obolibrary.org/obo/"):
        id = iri.split("/")[-1].replace("_", ":")

    return id


class OntologyImport(BaseModel):
    id: str
    iri: str | None
    root_id: TermIdentifier | None = None
    intermediates: Literal["all", "minimal"] | None = None
    version_iri: Optional[str] = None
    imported_terms: List[TermIdentifier] = []
    prefixes: List[Tuple[str, str]] = []
    excluding: List[TermIdentifier] = []


class ExcelOntology:
    _logger = logging.getLogger(__name__)
    _terms: List[UnresolvedTerm]
    _relations: List[UnresolvedRelation]
    _imports: List[OntologyImport]
    _used_relations: Set[UnresolvedRelation]
    _discard_status: List[str]
    _ignore_status: List[str]

    _iri: Optional[str]
    _version_iri: Optional[str]

    def __init__(
        self,
        iri: Optional[str] = None,
        version_iri: Optional[str] = None,
        *,
        ignore_terms_with_status: Optional[List[str]] = None,
        discard_terms_with_status: Optional[List[str]] = None,
    ):
        """
        Initialises a new instance of an ExcelOntology

        :param Optional[str] iri: IRI of the ontology
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
            ignore_terms_with_status = ["obsolete", "pre-proposed"]
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
        return [
            TermIdentifier(t.id, t.label)
            for o in self._imports
            for t in o.imported_terms
        ]

    def terms(self) -> List[Term]:
        return [
            term
            for t in self._terms
            if (term := t.as_resolved_term()) is not None
            and lower(t.curation_status()) not in self._discard_status
            and lower(t.curation_status()) not in self._ignore_status
        ]

    def term_by_label(self, label: str) -> Optional[Term | TermIdentifier]:
        return next(
            iter(t for t in (self.terms() + self.imported_terms()) if t.label == label),
            None,
        )

    def find_term_id(self, label: str) -> Optional[str]:
        return next(
            (t.id for t in (self._terms + self.imported_terms()) if t.label == label),
            None,
        )

    def find_term_label(self, id: str) -> Optional[str]:
        return next(
            (t.label for t in (self._terms + self.imported_terms()) if t.id == id), None
        )

    def term_by_id(self, id: str | None) -> Optional[Term]:
        return next(iter(t for t in (self.terms()) if t.id == id), None)

    def _term_by_id(self, id: str) -> Optional[UnresolvedTerm]:
        return next(iter(t for t in self._terms if t.id == id), None)

    def _term_by_label(self, label: str) -> Optional[UnresolvedTerm]:
        return next(iter(t for t in self._terms if t.label == label), None)

    def _raw_term_by_id(
        self, id: str, exclude: Optional[UnresolvedTerm] = None
    ) -> Optional[Union[UnresolvedTerm, TermIdentifier]]:
        terms_ = [
            t
            for t in (self._terms + self.imported_terms())
            if t.id == id and (exclude is None or exclude != t)
        ]
        terms_.sort(
            key=lambda t: (
                1
                if isinstance(t, UnresolvedTerm)
                and lower(t.curation_status()) in self._ignore_status
                else 0
            )
        )
        return next(iter(terms_), None)

    def _raw_relation_by_id(
        self, id: str, exclude: Optional[UnresolvedRelation] = None
    ) -> Optional[Union[UnresolvedRelation, TermIdentifier]]:
        relations_ = [
            r
            for r in (self._relations + self.imported_terms())
            if r.id == id and (exclude is None or exclude != r)
        ]
        relations_.sort(key=lambda r: 1 if isinstance(r, UnresolvedRelation) else 0)
        return next(iter(relations_), None)

    def relations(self) -> List[Relation]:
        return [r.as_resolved() for r in self._relations if not r.is_unresolved()]

    @with_result_context_method
    def _parse_term(
        self,
        ctx: ResultContext,
        row: list[tuple[ColumnMapping, str]],
        err_default: dict,
    ) -> UnresolvedTerm:
        ctx.log.template = err_default
        term = UnresolvedTerm()
        unprocessable_columns = []
        for col, val in row:
            if str_empty(val):
                continue

            if not col.valid(val):
                ctx.log.error(
                    column=col.get_name(),
                    type="invalid-value",
                    msg=f"Invalid value '{val}'",
                )
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
                term.label = col.get_value(val)
            elif isinstance(col, RelationColumnMapping):
                term.relations += col.get_value(val)
            # TODO: SYNONYMS field
            elif isinstance(col, ParentMapping):
                term.sub_class_of.append(col.get_value(val))
            elif col not in unprocessable_columns:
                ctx.log.warning(
                    column=col.get_name(),
                    type="unprocessable-column",
                    msg=f"The column '{col.get_name()}' could not be processed",
                )
                unprocessable_columns.append(col)

        if lower(term.curation_status()) in self._discard_status:
            self._logger.debug(
                f"Discarding {lower(term.curation_status())} term '{term.label}' ({term.id})'"
            )
        # elif
        # If a term has no id, label, or parents it is probably an empty line.
        # Ignore it but issue a warning.
        elif (
            str_empty(term.id) and str_empty(term.label) and not any(term.sub_class_of)
        ):
            ctx.log.warning(type="incomplete-term", msg="Empty or incomplete term")
        else:
            return term

        ctx.fail()

    @with_result_context_method
    def _parse_import(
        self,
        ctx: ResultContext,
        row: list[tuple[ColumnMapping, str]],
        err_default: dict,
    ) -> OntologyImport:
        ctx.log.template = err_default
        ontology = OntologyImport.model_construct()
        unprocessable_columns = []
        for col, val in row:
            if str_empty(val):
                continue

            if not col.valid(val):
                ctx.log.error(
                    column=col.get_name(),
                    type="invalid-value",
                    msg=f"Invalid value '{val}'",
                )
                continue

            if col.get_kind() == ColumnMappingKind.ONTOLOGY_ID:
                ontology.id = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.ONTOLOGY_IRI:
                ontology.iri = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.VERSION_IRI:
                ontology.version_iri = col.get_value(val)
            elif col.get_kind() == ColumnMappingKind.ROOT_ID and isinstance(
                col, TermMapping
            ):
                ontology.root_id = col.get_value(val)[0].assert_resolved_identifier()
            elif col.get_kind() == ColumnMappingKind.EXCLUDED_IMPORT_ID and isinstance(
                col, TermMapping
            ):
                ontology.excluding += [
                    v.assert_resolved_identifier() for v in col.get_value(val)
                ]
            elif col.get_kind() == ColumnMappingKind.IMPORTED_ID and isinstance(
                col, TermMapping
            ):
                ontology.imported_terms = [
                    v.assert_resolved_identifier() for v in col.get_value(val)
                ]
            elif (
                col.get_kind() == ColumnMappingKind.PLAIN
                and col.get_name().lower() == "intermediates"
            ):
                ontology.intermediates = col.get_value(val)
            elif isinstance(col, PrefixColumnMapping):
                ontology.prefixes = col.get_value(val)
            elif col not in unprocessable_columns:
                ctx.log.warning(
                    column=col.get_name(),
                    type="unprocessable-column",
                    msg=f"The column '{col.get_name()}' could not be processed",
                )
                unprocessable_columns.append(col)

        OntologyImport.model_validate(ontology)

        return ontology

    @with_result_context_method
    def _parse_relation(
        self,
        ctx: ResultContext,
        row: list[tuple[ColumnMapping, str]],
        err_default: dict,
    ) -> UnresolvedRelation:
        ctx.log.template = err_default
        relation = UnresolvedRelation(owl_property_type=OWLPropertyType.ObjectProperty)
        unprocessable_columns = []
        for col, val in row:
            if str_empty(val):
                continue

            if not col.valid(val):
                ctx.log.error(
                    column=col.get_name(),
                    type="invalid-value",
                    msg=f"Invalid value '{val}'",
                )
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
                ctx.log.warning(
                    column=col.get_name(),
                    type="unprocessable-column",
                    msg=f"The column '{col.get_name()}' could not be processed",
                )
                unprocessable_columns.append(col)

        return relation

    def add_term(self, term: Term):
        self._used_relations = set.union(
            self._used_relations,
            {UnresolvedRelation(r.id, r.label) for r, _ in term.relations},
        )
        self._terms.append(UnresolvedTerm(**term.__dict__))

    @with_result_context_method
    def add_imported_terms(
        self,
        ctx: ResultContext,
        name: str,
        file: Union[bytes, str, BytesIO],
        schema: Optional[Schema] = None,
    ) -> tuple[()]:
        if schema is None:
            schema = DEFAULT_IMPORT_SCHEMA

        data, mapped = ctx.unwrap(self._open_excel(name, file, schema))

        ctx.log.template = dict(file=name)

        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            parse_result = self._parse_import(
                [(m, c) for m, c in zip(mapped, row) if m is not None],
                dict(row=row_idx, origin=origin),
            )
            ctx.attempt(parse_result)

            if is_successful(parse_result):
                ontology: OntologyImport = parse_result.value
                # ontology.origin = (name, row_idx)
                self._imports.append(ontology)

        return ()

    @with_result_context_method
    def import_other_excel_ontology(self, ctx: ResultContext, other: Self) -> tuple[()]:
        ctx.log.template = dict(file=other._iri)
        imported_terms = []
        for term in other._terms + other._relations:
            if (resolved_term := term.as_resolved_identifier()) is not None:
                imported_terms.append(resolved_term)

        new_id = (
            other._iri
            if other._iri is not None
            else f"excel-import-{len(self._imports) + 1}"
        )
        ontology = OntologyImport(
            id=new_id, iri=f"ose://{new_id}", imported_terms=[t for t in imported_terms]
        )
        self._imports.append(ontology)

        return ()

    @with_result_context_method
    def import_excel_ontology_from_file(
        self,
        ctx: ResultContext,
        name: str,
        file: Union[bytes, str, BytesIO],
        schema: Optional[Schema] = None,
    ) -> tuple[()]:
        imported_terms = []
        data, mapped = ctx.unwrap(self._open_excel(name, file, schema))
        ctx.log.template = dict(file=name)
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            parse_result = self._parse_term(
                [(m, c) for m, c in zip(mapped, row) if m is not None],
                dict(row=row_idx, origin=origin),
            )

            ctx.attempt(parse_result)

            if is_successful(parse_result):
                term = parse_result.value.identifier()

                if (resolved := term.as_resolved_identifier()) is not None:
                    imported_terms.append(resolved)
                else:
                    ctx.log.warning(
                        type="incomplete-term",
                        msg=f"Unresolved term '{term}' in import '{name}'",
                    )

        ontology = OntologyImport(
            id=name, iri=f"ose://{name}", imported_terms=[t for t in imported_terms]
        )
        self._imports.append(ontology)

        return ()

    def merge_with(self, other: Self) -> None:
        self._terms += other._terms
        self._used_relations = set.union(self._used_relations, other._used_relations)
        self._imports += other._imports
        self._relations += other._relations

    @with_result_context_method
    def add_terms_from_list(
        self,
        ctx: ResultContext,
        data: list[list[str]],
        header: list[str],
        schema: Optional[Schema] = None,
        origin: Optional[str] = None,
    ) -> tuple[()]:
        if schema is None:
            schema = DEFAULT_SCHEMA

        if origin is None:
            origin = "<from_list>"

        ctx.log.template = dict(file=origin)

        mapped: List[Optional[ColumnMapping]] = []
        for h in header:
            header_name = h.strip()
            mapping = schema.get_mapping(origin, header_name)

            mapped.append(mapping)

            if mapping is None and not schema.is_ignored(header_name):
                ctx.log.warning(type="unknown-column", column=header_name, sheet=origin)

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(c.as_unresolved_relation())

        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            result = self._parse_term(
                [(m, c) for m, c in zip(mapped, row) if m is not None],
                dict(row=row_idx, origin=(origin, row_idx)),
            )

            ctx.attempt(result)

            if is_successful(result):
                term = result.value
                term.origin = (origin, row_idx)
                self._terms.append(term)

        return ()

    @with_result_context_method
    def add_terms_from_excel(
        self,
        ctx: ResultContext,
        name: str,
        file: Union[bytes, str, BytesIO],
        schema: Optional[Schema] = None,
    ) -> tuple[()]:
        data, mapped = ctx.unwrap(self._open_excel(name, file, schema))

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(c.as_unresolved_relation())
        ctx.log.template = dict(file=name)
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            parse_result = self._parse_term(
                [(m, c) for m, c in zip(mapped, row) if m is not None],
                dict(row=row_idx, origin=origin),
            )

            ctx.attempt(parse_result)

            if is_successful(parse_result):
                term = parse_result.value
                term.origin = origin
                self._terms.append(term)

        return ()

    @with_result_context_method
    def add_relations_from_excel(
        self,
        ctx: ResultContext,
        name: str,
        file: Union[bytes, str, BytesIO],
        schema: Optional[Schema] = None,
    ) -> tuple[()]:
        data, mapped = ctx.unwrap(self._open_excel(name, file, schema))

        for c in mapped:
            if isinstance(c, RelationColumnMapping):
                self._used_relations.add(c.as_unresolved_relation())
        ctx.log.template = dict(file=name)
        for i, row in enumerate(data):
            row_idx = i + 2  # +1 for zerobased +1 for header
            origin = (name, row_idx)
            parse_result = self._parse_relation(
                [(m, c) for m, c in zip(mapped, row) if m is not None],
                dict(row=row_idx, origin=origin),
            )

            ctx.attempt(parse_result)

            if is_successful(parse_result):
                relation = parse_result.value
                relation.origin = (name, row_idx)

                self._relations.append(relation)

        return ()

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
                    term.sub_class_of.append(termid(id=new_parent))

    def apply_renamings(
        self, file: str, scope: Literal["self", "import", "all"] = "all"
    ) -> None:
        with open(file, "r") as f:
            rows = csv.reader(f)
            next(rows)

            for row in rows:
                # Skip potential ROBOT header
                if row[0] == "ID" or len(row) < 2:
                    continue

                id = row[0]
                label = row[1]

                term: TermIdentifier | UnresolvedTerm | None
                if scope == "self" or scope == "all":
                    term = self._term_by_id(id)

                    if term is not None:
                        term.label = label

                else:
                    term = next(
                        (
                            t
                            for i in self._imports
                            for t in i.imported_terms
                            if t.id == id
                        ),
                        None,
                    )

                    if term is not None:
                        term.label = label

    @with_result_context_method
    def _open_excel(
        self,
        ctx: ResultContext,
        origin: str,
        file: Union[bytes, str, BytesIO],
        schema: Optional[Schema] = None,
    ) -> Tuple[Iterator[Iterator[str]], List[ColumnMapping | None]]:
        ctx.log.template = dict(file=origin)
        if schema is None:
            schema = DEFAULT_SCHEMA
        if isinstance(file, bytes):
            file = BytesIO(file)

        wb = openpyxl.load_workbook(file)

        sheet: Worksheet | None = wb.active
        assert sheet is not None
        data = sheet.rows
        header = next(data)
        mapped: List[ColumnMapping | None] = []
        for h in header:
            if h.value is None:
                continue

            header_name = str(h.value).strip()
            mapping = schema.get_mapping(origin, header_name)
            if mapping is None and not schema.is_ignored(header_name):
                ctx.log.warning(
                    type="unknown-column",
                    column=header_name,
                    sheet=(
                        os.path.basename(file) if isinstance(file, str) else sheet.title
                    ),
                )

            mapped.append(mapping)

        rows = (("" if c.value is None else str(c.value) for c in row) for row in data)
        return (rows, mapped)

    @with_result_context_method
    def resolve(self, ctx: ResultContext) -> tuple[()]:
        imported = self.imported_terms()

        # Resolve terms
        for term in self._terms:
            if (
                lower(term.curation_status())
                in self._ignore_status + self._discard_status
            ):
                self._logger.debug(
                    f"Not resolving {term.curation_status()} term {term.label} ({term.id})"
                )
                continue

            if term.id is None or term.label is None:
                self._logger.error(
                    f"Term without id or label encountered. This should not happen. Term: {term}"
                )
                # continue

            if term.is_resolved():
                continue

            relation_values = [
                x for r, x in term.relations if isinstance(x, TermIdentifierBase)
            ]
            unresolved = [
                *term.sub_class_of,
                *term.disjoint_with,
            ] + relation_values
            unresolved = [i for i in unresolved if i.is_unresolved()]
            for unresolved_term in unresolved:
                matching_terms: list[TermIdentifierBase] = [
                    t
                    for t in (self._terms + imported)
                    if t != unresolved_term
                    and (
                        unresolved_term.label is not None
                        and unresolved_term.label == t.label
                        or unresolved_term.id is not None
                        and unresolved_term.id == t.id
                    )
                ]

                matching_terms.sort(
                    key=lambda t: (
                        1
                        if isinstance(t, UnresolvedTerm)
                        and (lower(t.curation_status()) in self._ignore_status)
                        else 0
                    )
                )

                for m in matching_terms:
                    unresolved_term.complement(
                        m if isinstance(m, TermIdentifierBase) else m.identifier()
                    )

        # Resolve relations
        for relation in self._relations:
            if not relation.is_unresolved():
                continue

            matching_import = next(
                (
                    t
                    for t in imported
                    if (
                        relation.label is not None
                        and relation.label == t.label
                        or relation.id is not None
                        and relation.id == t.id
                    )
                ),
                None,
            )

            if matching_import is not None:
                if matching_import.id is not None:
                    relation.id = matching_import.id
                if matching_import.label is not None:
                    relation.label = matching_import.label

            if relation.range and relation.range.is_unresolved():
                matching_terms = [
                    t
                    for t in (self._terms + imported)
                    if (
                        relation.range.label is not None
                        and relation.range.label == t.label
                        or relation.range.id is not None
                        and relation.range.id == t.id
                    )
                ]

                for m in matching_terms:
                    if (
                        isinstance(m, UnresolvedTerm)
                        and lower(m.curation_status())
                        in self._ignore_status + self._discard_status
                    ):
                        continue

                    relation.range.complement(
                        m if isinstance(m, TermIdentifierBase) else m.identifier()
                    )

            if relation.domain and relation.domain.is_unresolved():
                matching_terms = [
                    t
                    for t in (self._terms + imported)
                    if (
                        relation.domain.label is not None
                        and relation.domain.label == t.label
                        or relation.domain.id is not None
                        and relation.domain.id == t.id
                    )
                ]

                for m in matching_terms:
                    if (
                        isinstance(m, UnresolvedTerm)
                        and lower(m.curation_status())
                        in self._ignore_status + self._discard_status
                    ):
                        continue

                    relation.domain.complement(
                        m if isinstance(m, TermIdentifierBase) else m.identifier()
                    )

            for sub in relation.sub_property_of:
                matching_terms = [
                    t
                    for t in (self._relations + imported)
                    if (
                        sub.label is not None
                        and sub.label == t.label
                        or sub.id is not None
                        and sub.id == t.id
                    )
                ]

                for m in matching_terms:
                    if (
                        isinstance(m, TermBase)
                        and lower(m.curation_status())
                        in self._ignore_status + self._discard_status
                    ):
                        continue

                    sub.complement(m)

            for er in relation.equivalent_relations:
                matching_terms = [
                    t
                    for t in (self._terms + imported)
                    if (
                        er.label is not None
                        and er.label == t.label
                        or er.id is not None
                        and er.id == t.id
                    )
                ]

                for m in matching_terms:
                    if (
                        isinstance(m, UnresolvedTerm)
                        and lower(m.curation_status())
                        in self._ignore_status + self._discard_status
                    ):
                        continue

                    er.complement(m)

        # Resolve used relations
        replacements: List[Tuple[UnresolvedRelation, UnresolvedRelation]] = []
        for relation in self._used_relations:
            if relation.is_unresolved():
                matching = next(
                    (
                        r
                        for r in self._relations
                        if not r.is_unresolved()
                        and (r.label == relation.label or r.id == id)
                    ),
                    None,
                )

                if matching is not None:
                    replacements.append((relation, matching))
                    continue

                matching_term = next(
                    (
                        t
                        for i in self._imports
                        for t in i.imported_terms
                        if t.id == relation.id or t.label == relation.label
                    ),
                    None,
                )
                if matching_term is not None:
                    relation.id = matching_term.id
                    relation.label = matching_term.label

        for old, new in replacements:
            self._used_relations.remove(old)
            self._used_relations.add(new)

        for term in self._terms:
            for relation_term, _ in term.relations:
                if relation_term.is_unresolved():
                    used_relations = [
                        r
                        for r in self._used_relations
                        if (
                            r.label is None
                            or relation_term.label is None
                            or relation_term.label == r.label
                        )
                        and (
                            r.id is None
                            or relation_term.label is None
                            or relation_term.label == r.label
                        )
                    ]
                    for r in used_relations:
                        relation_term.complement(r.identifier())

        return ()

    @with_result_context_method
    def validate(
        self,
        ctx: ResultContext,
        only: Optional[List[DIAGNOSTIC_KIND]] = None,
        exclude: Optional[List[DIAGNOSTIC_KIND]] = None,
    ) -> tuple[()]:
        """
        Validate the loaded ontology. Checks for various errors such as unknown parents, related terms, duplicates, etc.

        :param only: List of errors or warning to report. If ``None``, all errors are reported
                     (if not excluded by `exclude`)
        :param exclude: List of errors to exclude. If ``None``, no errors are explicitly excluded.
        """

        def c(arg1: DIAGNOSTIC_KIND, arg2: Optional[DIAGNOSTIC_KIND] = None) -> bool:
            """
            Helper function to check if specific errors or warnings should be flagged
            """
            args = [a for a in [arg1, arg2] if a is not None]
            return (only is None or any(a in only for a in args)) and (
                exclude is None or not all(a in exclude for a in args)
            )

        imported_terms = set(t for i in self._imports for t in i.imported_terms)

        # To find duplicates store a list of terms with the same ID or label
        by_id: DefaultDict[str, List[Union[UnresolvedTerm, UnresolvedRelation]]] = (
            defaultdict(list)
        )
        by_label: DefaultDict[str, List[Union[UnresolvedTerm, UnresolvedRelation]]] = (
            defaultdict(list)
        )

        for term in self._terms:
            ctx.log.template = (
                {"row": term.origin[1], "origin": term.origin[0]}
                if term.origin is not None
                else {}
            )
            if (
                lower(term.curation_status())
                in self._ignore_status + self._discard_status
            ):
                self._logger.debug(
                    f"Not validating {term.curation_status()} term {term.label} ({term.id})"
                )
                continue

            if c("missing-label") and term.label is None:
                ctx.log.error(type="missing-label", term=term.__dict__)

            if c("missing-id") and term.id is None:
                ctx.log.error(type="missing-id", term=term.__dict__)

            term_id = term.identifier().assert_resolved_identifier()

            by_id[term_id.id].append(term)
            by_label[term_id.label].append(term)

            if (
                c("inconsistent-import", "missing-import")
                and lower(term.curation_status()) == "external"
                and term.identifier() not in imported_terms
            ):
                imported_term = next(
                    (
                        t
                        for t in imported_terms
                        if t.id == term.id or t.label == term.label
                    ),
                    None,
                )
                if imported_term is not None:
                    if c("inconsistent-import"):
                        ctx.log.warning(
                            type="inconsistent-import",
                            imported_term=imported_term,
                            term=term.__dict__,
                        )
                elif c("missing-import"):
                    ctx.log.warning(type="missing-import", term=term.__dict__)

            if c("no-parent") and len(term.sub_class_of) < 1:
                ctx.log.error(type="no-parent", term=term.__dict__)

            for p in term.sub_class_of:
                if c("unknown-parent") and p.is_unresolved():
                    ctx.log.error(
                        type="unknown-parent", term=term.__dict__, parent=p.__dict__
                    )
                elif (
                    c("missing-parent", "ignored-parent")
                    and (parent := p.as_resolved_identifier()) is not None
                ):
                    t = self._raw_term_by_id(parent.id)
                    if c("missing-parent") and t is None:
                        ctx.log.error(
                            type="missing-parent", term=term.__dict__, parent=p.__dict__
                        )
                    elif (
                        c("ignored-parent")
                        and isinstance(t, UnresolvedTerm)
                        and lower(t.curation_status()) in self._ignore_status
                    ):
                        ctx.log.error(
                            type="ignored-parent",
                            status=t.curation_status(),
                            term=term.__dict__,
                            parent=p.__dict__,
                        )

            for p in term.disjoint_with:
                if c("unknown-disjoint") and p.is_unresolved():
                    ctx.log.error(
                        type="unknown-disjoint",
                        term=term.__dict__,
                        disjoint_class=p.__dict__,
                    )
                elif (
                    c("missing-disjoint", "ignored-disjoint")
                    and (disjoint := p.as_resolved_identifier()) is not None
                ):
                    t = self._raw_term_by_id(disjoint.id)
                    if c("missing-disjoint") and t is None:
                        ctx.log.error(
                            type="missing-disjoint",
                            term=term.__dict__,
                            disjoint_class=p.__dict__,
                        )
                    elif (
                        c("ignored-disjoint")
                        and isinstance(t, UnresolvedTerm)
                        and lower(t.curation_status()) in self._ignore_status
                    ):
                        ctx.log.error(
                            type="ignored-disjoint",
                            status=t.curation_status(),
                            term=term.__dict__,
                            disjoint_class=p.__dict__,
                        )

            for relation, value in term.relations:
                if isinstance(value, TermIdentifier):
                    if c("unknown-relation-value") and value.is_unresolved():
                        ctx.log.error(
                            type="unknown-relation-value",
                            relation=relation,
                            value=value,
                            term=term.__dict__,
                        )
                    else:
                        t = self._raw_term_by_id(value.id)
                        if c("missing-relation-value") and t is None:
                            ctx.log.error(
                                type="missing-relation-value",
                                term=term.__dict__,
                                relation=relation,
                                value=value,
                            )
                        elif (
                            c("ignored-relation-value")
                            and isinstance(t, UnresolvedTerm)
                            and lower(t.curation_status()) in self._ignore_status
                        ):
                            ctx.log.error(
                                type="ignored-relation-value",
                                status=t.curation_status(),
                                term=term.__dict__,
                                relation=relation,
                                value=value,
                            )

        for relation in self._relations:
            ctx.log.template = (
                {"row": relation.origin[1]} if relation.origin is not None else {}
            )
            if c("missing-label") and relation.label is None:
                ctx.log.error(type="missing-label", relation=relation.__dict__)

            if c("missing-id") and relation.id is None:
                ctx.log.error(type="missing-id", relation=relation.__dict__)

            relation_id = relation.identifier().assert_resolved_identifier()

            by_id[relation_id.id].append(relation)
            by_label[relation_id.label].append(relation)

            if relation.domain:
                if c("unknown-domain") and relation.domain.is_unresolved():
                    ctx.log.error(type="unknown-domain", relation=relation.__dict__)
                elif (domain := relation.domain.as_resolved_identifier()) is not None:
                    t = self._raw_term_by_id(domain.id)
                    if c("missing-domain") and t is None:
                        ctx.log.error(
                            type="missing-domain",
                            relation=relation.__dict__,
                            domain=domain.__dict__,
                        )
                    elif (
                        c("ignored-domain")
                        and isinstance(t, UnresolvedTerm)
                        and lower(t.curation_status()) in self._ignore_status
                    ):
                        ctx.log.error(
                            type="ignored-domain",
                            status=t.curation_status(),
                            relation=relation.__dict__,
                            domain=domain.__dict__,
                        )

            if relation.range:
                if c("unknown-range") and relation.range.is_unresolved():
                    ctx.log.error(type="unknown-range", relation=relation.__dict__)
                elif (range := relation.range.as_resolved_identifier()) is not None:
                    t = self._raw_term_by_id(range.id)
                    if c("missing-range") and t is None:
                        ctx.log.error(
                            type="missing-range",
                            relation=relation.__dict__,
                            range=range.__dict__,
                        )
                    elif (
                        c("ignored-range")
                        and isinstance(t, UnresolvedTerm)
                        and lower(t.curation_status()) in self._ignore_status
                    ):
                        ctx.log.error(
                            type="ignored-range",
                            status=t.curation_status(),
                            relation=relation.__dict__,
                            range=range.__dict__,
                        )

            for p in relation.sub_property_of:
                if c("unknown-parent") and p.is_unresolved():
                    ctx.log.error(
                        type="unknown-parent", term=relation.__dict__, parent=p.__dict__
                    )
                elif (parent := p.as_resolved_identifier()) is not None:
                    rt = self._raw_relation_by_id(parent.id)
                    if c("missing-parent") and rt is None:
                        ctx.log.error(
                            type="missing-parent",
                            term=relation.__dict__,
                            parent=p.__dict__,
                        )

            for r, value in relation.relations:
                if isinstance(value, TermIdentifier):
                    if c("unknown-relation-value") and value.is_unresolved():
                        ctx.log.error(
                            type="unknown-relation-value",
                            relation=r,
                            value=value,
                            term=relation.__dict__,
                        )
                    else:
                        t = self._raw_term_by_id(value.id)
                        if c("missing-relation-value") and t is None:
                            ctx.log.error(
                                type="missing-relation-value",
                                term=relation.__dict__,
                                relation=r,
                                value=value,
                            )
                        elif (
                            c("ignored-relation-value")
                            and isinstance(t, UnresolvedTerm)
                            and lower(t.curation_status()) in self._ignore_status
                        ):
                            ctx.log.error(
                                type="ignored-relation-value",
                                status=t.curation_status(),
                                term=relation.__dict__,
                                relation=r,
                                value=value,
                            )

        # Check that all relations used in the spreadsheets (column headers) are defined
        for relation in self._used_relations:
            if relation.owl_property_type == OWLPropertyType.Internal:
                continue

            ctx.log.template = (
                {"row": relation.origin[1]} if relation.origin is not None else {}
            )
            if relation.is_unresolved():
                ctx.log.error(type="unknown-relation", relation=relation.__dict__)

        # Check for duplicates
        if c("duplicate"):
            for k, items in itertools.chain(by_id.items(), by_label.items()):
                duplicates = [
                    item
                    for item in items
                    if not isinstance(item, UnresolvedTerm)
                    or item.curation_status() not in self._ignore_status
                ]
                if len(duplicates) > 1:
                    mismatches = []
                    for a, b in itertools.combinations(duplicates, 2):
                        if (
                            a.id is None
                            or b.id is None
                            or a.label is None
                            or b.label is None
                        ):
                            continue
                        if a.label != b.label:
                            mismatches.append(("label", a, b))
                        if a.id != b.id:
                            mismatches.append(("id", a, b))
                        if isinstance(a, UnresolvedTerm) and isinstance(
                            b, UnresolvedTerm
                        ):
                            definition_a = a.definition()
                            definition_a = (
                                (definition_a.replace("<", "").replace(">", ""))
                                if definition_a is not None
                                else ""
                            )
                            definition_b = b.definition()
                            definition_b = (
                                (definition_b.replace("<", "").replace(">", ""))
                                if definition_b is not None
                                else ""
                            )
                            if not str_space_eq(definition_a, definition_b):
                                mismatches.append(("definition", a, b))
                            if not str_space_eq(
                                a.curation_status(), b.curation_status()
                            ):
                                mismatches.append(("curation status", a, b))
                        elif isinstance(a, UnresolvedRelation) and isinstance(
                            b, UnresolvedRelation
                        ):
                            pass
                        else:
                            mismatches.append(("type", a, b))
                    if len(mismatches) > 0:
                        ctx.log.error(
                            type="duplicate",
                            duplicate_field="id" if k in by_id else "label",
                            duplicate_value=k,
                            duplicates=list(
                                set(x for _, a, b in mismatches for x in [a, b])
                            ),
                            mismatches=[
                                dict(field=f, a=a, b=b) for f, a, b in mismatches
                            ],
                        )

        return ()

    def remove_duplicates(self) -> int:
        to_remove: List[UnresolvedTerm] = []
        hashset: Set[TermIdentifier] = set()
        for term in self._terms:
            if term.identifier() in hashset:
                to_remove.append(term)
            else:
                hashset.add(term.identifier(TermIdentifier))

        for term in to_remove:
            self._terms.remove(term)

        return len(to_remove)

    def iri(self) -> str | None:
        return self._iri

    def add_relation(self, relation: Relation):
        self._relations.append(UnresolvedRelation(**dataclasses.asdict(relation)))

    @classmethod
    def from_excel(
        cls,
        iri: str,
        files: list[
            Tuple[str, Union[bytes, str, BytesIO], Literal["classes", "relations"]]
        ],
    ):
        ontology = ExcelOntology(iri)
        for name, file, kind in files:
            if kind == "classes":
                ontology.add_terms_from_excel(name, file)
            elif kind == "relations":
                ontology.add_relations_from_excel(name, file)

        return ontology

    @classmethod
    @with_result_context_method
    def from_owl(
        cls,
        ctx: ResultContext,
        externals_owl: str,
        prefixes: Dict[str, str],
        origin: str = "<external>",
    ) -> Self:
        ctx.log.template = dict(file=externals_owl, origin=origin)
        
        ontology = ho.open_ontology(externals_owl)

        # Add default prefixes
        ontology.prefix_mapping.add_default_prefix_names()

        self = cls(str(ontology.get_iri()))
        for p, prefix_iri in prefixes.items():
            ontology.prefix_mapping.add_prefix(p, prefix_iri)

        for c in ontology.get_classes():
            id = get_id(ontology, c)

            labels = ontology.get_annotations(c, constants.RDFS_LABEL)

            if id is None:
                ctx.log.warning(
                    type="unknown-id",
                    msg=f'Unable to determine id of external term "{c}"',
                )
            if len(labels) == 0:
                ctx.log.warning(
                    type="unknown-label",
                    msg=f'Unable to determine label of external term "{c}"',
                )

            superclasses = ontology.get_superclasses(c)
            superclass_ids = [
                termid(
                    id=get_id(ontology, s),
                    label=ontology.get_annotation(s, constants.RDFS_LABEL),
                )
                for s in superclasses
            ]
            superclass_terms = [
                s.assert_resolved_identifier()
                for s in superclass_ids
                if s.is_resolved()
            ]

            if id is not None:
                for label in labels:
                    self.add_term(
                        Term(
                            id=id,
                            label=label,
                            origin=(origin, -1),
                            relations=[],
                            sub_class_of=superclass_terms,
                            equivalent_to=[],
                            disjoint_with=[],
                        )
                    )

        for r in ontology.get_object_properties():
            id = ontology.get_id_for_iri(r)
            op_label = ontology.get_annotation(r, constants.RDFS_LABEL)

            if id is None:
                ctx.log.warning(
                    type="unknown-id",
                    msg=f'Unable to determine id of {origin} relation "{r}"',
                )
            if op_label is None:
                ctx.log.warning(
                    type="unknown-label",
                    msg=f'Unable to determine label of {origin} relation "{r}"',
                )

            if id is not None and op_label is not None:
                self.add_relation(
                    Relation(
                        id=id,
                        label=op_label,
                        origin=(origin, -1),
                        equivalent_relations=[],
                        inverse_of=[],
                        relations=[],
                        owl_property_type=OWLPropertyType.ObjectProperty,
                        sub_property_of=[],
                        domain=None,
                        range=None,
                    )
                )

        return self

    @with_result_context_method
    def to_owl(
        self, ctx: ResultContext, prefixes: Dict[str, str]
    ) -> ho.PyIndexedOntology:
        o = ho.PyIndexedOntology()
        o.prefix_mapping.add_default_prefix_names()
        for p, prefix_iri in prefixes.items():
            o.prefix_mapping.add_prefix(p, prefix_iri)

        used_relations = [
            u.as_resolved() for u in self._used_relations if u.is_resolved()
        ]
        propery_kinds = {
            r.identifier(): r.owl_property_type
            for r in used_relations + self.relations()
        }

        for term in self.terms():
            if term.id is None or term.label is None:
                continue

            c = o.class_(term.id)
            ciri = c.first
            o.declare_class(ciri)
            o.add_component(
                ho.model.AnnotationAssertion(
                    ciri,
                    ho.model.Annotation(
                        o.annotation_property(constants.RDFS_LABEL),
                        ho.model.SimpleLiteral(term.label),
                    ),
                )
            )

            for parent in term.sub_class_of:
                o.add_component(ho.model.SubClassOf(c, o.class_(parent.id)))

            for disjoint in term.disjoint_with:
                o.add_component(ho.model.DisjointClasses([c, o.class_(disjoint.id)]))

            for eq in term.equivalent_to:
                raise NotImplementedError("TODO: Require later pho which parses MS")

            for term_relation, value in term.relations:
                riri = o.iri(term_relation.id)

                match propery_kinds.get(term_relation):
                    case OWLPropertyType.ObjectProperty:
                        if isinstance(value, TermIdentifier):
                            op = o.object_property(riri)
                            o.declare_object_property(riri)
                            o.add_component(
                                ho.model.SubClassOf(c, op.some(o.class_(value.id)))
                            )
                        else:
                            ctx.log.warning(
                                type="wrong-relation-value-type",
                                term=term.__dict__,
                                relation=term_relation.__dict__,
                                value=value,
                                message=f"Expected another entity for ObjectProperty relation, got {type(value)}",
                            )
                    case OWLPropertyType.DataProperty:
                        if isinstance(value, TermIdentifier):
                            dp = o.data_property(riri)
                            o.declare_data_property(riri)
                            o.add_component(
                                ho.model.SubClassOf(
                                    c,
                                    ho.model.DataSomeValuesFrom(
                                        dp, ho.model.Datatype(o.iri(value.id))
                                    ),
                                )
                            )
                        else:
                            ctx.log.warning(
                                type="wrong-relation-value-type",
                                term=term.__dict__,
                                relation=term_relation.__dict__,
                                value=value,
                                message=f"Expected a datatype for DataProperty relation, got {type(value)}",
                            )
                    case OWLPropertyType.AnnotationProperty:
                        if isinstance(value, str):
                            ap = o.annotation_property(riri)
                            o.declare_annotation_property(riri)
                            o.add_component(
                                ho.model.AnnotationAssertion(
                                    ciri,
                                    ho.model.Annotation(
                                        ap, ho.model.SimpleLiteral(value)
                                    ),
                                )
                            )
                        else:
                            ctx.log.warning(
                                type="wrong-relation-value-type",
                                term=term.__dict__,
                                relation=term_relation.__dict__,
                                value=value,
                                message=f"Expected a string for AnnotationProperty relation, got {type(value)}",
                            )
                    case OWLPropertyType.Internal:
                        pass
                    case _:
                        ctx.log.warning(
                            type="unknown-relation-type",
                            term=term.__dict__,
                            relation=term_relation.__dict__,
                            value=value,
                            message=f"Unknown relation type {propery_kinds.get(term_relation)}",
                        )

        for relation in self.relations():
            riri = o.iri(relation.id)

            match relation.owl_property_type:
                case OWLPropertyType.ObjectProperty:
                    op = o.object_property(riri)
                    o.declare_object_property(riri)

                    if relation.domain and relation.domain.is_resolved():
                        o.add_component(
                            ho.model.ObjectPropertyDomain(
                                op, o.class_(relation.domain.id)
                            )
                        )
                    if relation.range and relation.range.is_resolved():
                        o.add_component(
                            ho.model.ObjectPropertyRange(
                                op, o.class_(relation.range.id)
                            )
                        )

                    for sub in relation.sub_property_of:
                        o.add_component(
                            ho.model.SubObjectPropertyOf(op, o.object_property(sub.id))
                        )

                    for eq_r in relation.equivalent_relations:
                        o.add_component(
                            ho.model.EquivalentObjectProperties(
                                [op, o.object_property(eq_r.id)]
                            )
                        )

                    for inv in relation.inverse_of:
                        o.add_component(
                            ho.model.InverseObjectProperties(
                                op, o.object_property(inv.id)
                            )
                        )

                case OWLPropertyType.DataProperty:
                    dp = o.data_property(riri)
                    o.declare_data_property(riri)

                    if relation.domain and relation.domain.is_resolved():
                        o.add_component(
                            ho.model.DataPropertyDomain(
                                dp, o.class_(relation.domain.id)
                            )
                        )
                    if relation.range and relation.range.is_resolved():
                        o.add_component(
                            ho.model.DataPropertyRange(
                                dp, ho.model.Datatype(o.iri(relation.range.id))
                            )
                        )

                    for sub in relation.sub_property_of:
                        o.add_component(
                            ho.model.SubDataPropertyOf(dp, o.data_property(sub.id))
                        )

                    for eq_r in relation.equivalent_relations:
                        o.add_component(
                            ho.model.EquivalentDataProperties(
                                [dp, o.data_property(eq_r.id)]
                            )
                        )
                case OWLPropertyType.AnnotationProperty:
                    ap = o.annotation_property(riri)
                    o.declare_annotation_property(riri)

            o.add_component(
                ho.model.AnnotationAssertion(
                    riri,
                    ho.model.Annotation(
                        o.annotation_property(constants.RDFS_LABEL),
                        ho.model.SimpleLiteral(relation.label),
                    ),
                )
            )

            for r, value in relation.relations:
                riri = o.iri(r.id)

                match propery_kinds.get(r):
                    case OWLPropertyType.ObjectProperty | OWLPropertyType.DataProperty:
                        ctx.log.error(
                            type="relation-on-relation",
                            relation=relation.__dict__,
                            sub_relation=r.__dict__,
                            value=value,
                            message=f"{propery_kinds.get(r)} relation {r.label} ({r.id}) ",
                        )
                    case OWLPropertyType.AnnotationProperty:
                        if isinstance(value, str):
                            ap = o.annotation_property(riri)
                            o.declare_annotation_property(riri)
                            o.add_component(
                                ho.model.AnnotationAssertion(
                                    ciri,
                                    ho.model.Annotation(
                                        ap, ho.model.SimpleLiteral(value)
                                    ),
                                )
                            )
                        else:
                            ctx.log.warning(
                                type="wrong-relation-value-type",
                                term=term.__dict__,
                                relation=relation.__dict__,
                                value=value,
                                message=f"Expected a string for AnnotationProperty relation, got {type(value)}",
                            )
                    case OWLPropertyType.Internal:
                        pass
                    case _:
                        ctx.log.warning(
                            type="unknown-relation-type",
                            term=term.__dict__,
                            relation=relation.__dict__,
                            value=value,
                            message=f"Unknown relation type {propery_kinds.get(r)}",
                        )

        return o

    def to_excel(self, include_origin: bool = False) -> Workbook:
        relations = self.used_relations()

        wb = Workbook()
        ws: Worksheet = wb.active  # type: ignore

        header = ["ID", "Label", "Parent", "Disjoint classes", "Logical definition"] + [
            (r.label if r.id is None else f"REL '{r.label}'") for r in relations
        ]
        if include_origin:
            header += ["origin"]

        ws.append(header)
        
        terms = sorted(self._terms, key=lambda t: (t.origin[0], t.origin[1]) if t.origin is not None else ("", -1))

        for term in terms:
            row = [
                term.id,
                term.label,
                "; ".join(
                    f"{s.label} [{s.id}]" if s.id is not None else s.label
                    for s in term.sub_class_of
                    if s.label is not None
                ),
                "; ".join(
                    f"{s.label} [{s.id}]" if s.id is not None else s.label
                    for s in term.disjoint_with
                    if s.label is not None
                ),
                "; ".join(term.equivalent_to),
            ] + [
                term.get_relation_value(i)
                for r in relations
                if (i := r.as_resolved_identifier()) is not None
            ]

            if include_origin:
                row += [
                    (
                        f"{term.origin[0]}:{term.origin[1]}"
                        if term.origin is not None
                        else ""
                    )
                ]

            ws.append(row)

        return wb
