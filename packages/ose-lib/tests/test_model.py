import re

import pytest
from pydantic import ValidationError

from ose.schema.ColumnMapping import (
    ChoiceColumnMapping,
    ColumnMappingKind,
    IRIMapping,
    LabelMapping,
    ParentMapping,
    PrefixColumnMapping,
    RelationColumnMapping,
    RelationRef,
    SimpleColumnMapping,
    TermMapping,
)
from ose.schema.Relation import OWLPropertyType, UnresolvedRelation
from ose.schema.Schema import BUILTIN_SCHEMAS, DEFAULT_IMPORT_SCHEMA, DEFAULT_SCHEMA, Schema, resolve_schema
from ose.schema.Term import UnresolvedTerm
from ose.schema.TermIdentifier import (
    TermIdentifier,
    TermIdentifierWithId,
    TermIdentifierWithLabel,
    UnresolvedTermIdentifier,
    termid,
)

DEFINITION = TermIdentifier(id="IAO:0000115", label="definition")
CURATION_STATUS = TermIdentifier(id="IAO:0000114", label="has curation status")
SYNONYM = TermIdentifier(id="IAO:0000118", label="alternative label")


# --- TermIdentifier ---------------------------------------------------------


def test_termid_picks_most_specific_type():
    assert type(termid(id="A:1", label="a")) is TermIdentifier
    assert type(termid(id="A:1")) is TermIdentifierWithId
    assert type(termid(label="a")) is TermIdentifierWithLabel
    assert type(termid()) is UnresolvedTermIdentifier


def test_termid_resolution_state():
    assert termid(id="A:1", label="a").is_resolved()
    assert termid(id="A:1").is_unresolved()
    assert termid(label="a").is_unresolved()


def test_casts_return_none_when_field_missing():
    assert termid(label="a").as_with_id() is None
    assert termid(id="A:1").as_with_label() is None
    assert termid(id="A:1").as_resolved_identifier() is None
    assert termid(id="A:1", label="a").as_resolved_identifier() == TermIdentifier("A:1", "a")


def test_assert_casts_raise_when_field_missing():
    assert termid(id="A:1", label="a").assert_resolved_identifier() == TermIdentifier("A:1", "a")
    with pytest.raises(ValueError):
        termid(id="A:1").assert_resolved_identifier()
    with pytest.raises(ValueError):
        termid(label="a").assert_id()


def test_complement_fills_missing_fields_only():
    t = UnresolvedTermIdentifier(label="a")
    t.complement(TermIdentifier("A:1", "other"))
    assert (t.id, t.label) == ("A:1", "a")


def test_identifier_equality_hash_and_order():
    assert TermIdentifier("A:1", "a") == UnresolvedTermIdentifier("A:1", "a")
    assert TermIdentifier("A:1", "a") != TermIdentifier("A:1", "b")
    assert TermIdentifier("A:1", "a") != "A:1"
    assert len({TermIdentifier("A:1", "a"), UnresolvedTermIdentifier("A:1", "a")}) == 1
    assert sorted([termid(id="B:1"), termid(label="x"), termid(id="A:1")]) == [
        termid(label="x"),
        termid(id="A:1"),
        termid(id="B:1"),
    ]


# --- Term ---------------------------------------------------------------------


def make_term(**kwargs) -> UnresolvedTerm:
    defaults = dict(id="EX:1", label="thing", origin=("f.xlsx", 2))
    return UnresolvedTerm(**{**defaults, **kwargs})


def test_term_annotation_accessors():
    term = make_term(
        relations=[
            (CURATION_STATUS, " External "),
            (DEFINITION, " A thing. "),
            (SYNONYM, "stuff "),
            (SYNONYM, "object"),
        ]
    )

    assert term.curation_status() == "External"
    assert term.is_external() is True
    assert term.definition() == "A thing."
    assert term.synonyms() == ["stuff", "object"]
    assert make_term().curation_status() is None
    assert make_term().is_external() is None
    assert make_term(relations=[(CURATION_STATUS, "Published")]).is_external() is False


def test_term_definition_setter_replaces_or_appends():
    term = make_term(relations=[(DEFINITION, "old")])
    assert term.definition("new") == "new"
    assert term.definition() == "new"
    assert len(term.relations) == 1

    empty = make_term()
    empty.definition("fresh")
    assert empty.relations == [(DEFINITION, "fresh")]


def test_term_relation_values():
    term = make_term(relations=[(DEFINITION, "d"), (SYNONYM, "s1"), (SYNONYM, "s2")])
    assert term.get_relation_values(SYNONYM) == ["s1", "s2"]
    assert term.get_relation_value(DEFINITION) == "d"
    assert term.get_relation_value(CURATION_STATUS) is None


def test_unresolved_term_resolution():
    parent = UnresolvedTermIdentifier(label="parent")
    term = make_term(sub_class_of=[parent])
    assert term.is_unresolved()
    assert term.as_resolved_term() is None

    parent.id = "EX:0"
    assert term.is_resolved()
    resolved = term.as_resolved_term()
    assert resolved is not None and [(p.id, p.label) for p in resolved.sub_class_of] == [("EX:0", "parent")]

    assert UnresolvedTerm(label="no id", origin=("f", 1)).is_unresolved()
    assert make_term(origin=None).is_unresolved()


def test_term_equality_ignores_order():
    a = make_term(sub_class_of=[termid(id="EX:2", label="b"), termid(id="EX:3", label="c")])
    b = make_term(sub_class_of=[termid(id="EX:3", label="c"), termid(id="EX:2", label="b")])
    resolved_a, resolved_b = a.as_resolved_term(), b.as_resolved_term()
    assert resolved_a == resolved_b
    assert hash(resolved_a) == hash(resolved_b)


# --- Relation -----------------------------------------------------------------


def test_unresolved_relation_resolution():
    rel = UnresolvedRelation(
        id="EX:9",
        label="has part",
        owl_property_type=OWLPropertyType.ObjectProperty,
        origin=("r.xlsx", 2),
        domain=UnresolvedTermIdentifier(label="thing"),
    )
    assert rel.is_unresolved()
    assert rel.to_resolved() is None
    with pytest.raises(ValueError):
        rel.as_resolved()

    rel.domain.id = "EX:1"  # type: ignore[union-attr]
    resolved = rel.as_resolved()
    assert resolved.identifier() == TermIdentifier("EX:9", "has part")
    assert resolved.domain is not None and (resolved.domain.id, resolved.domain.label) == ("EX:1", "thing")

    assert UnresolvedRelation(id="EX:9", label="x", origin=("r", 1)).is_unresolved()  # no property type


def test_unresolved_relation_is_hashable_by_value():
    a = UnresolvedRelation(id="EX:9", label="has part")
    b = UnresolvedRelation(id="EX:9", label="has part")
    assert len({a, b}) == 1


# --- ColumnMapping ------------------------------------------------------------


def test_parent_mapping():
    m = ParentMapping(columns=["Parent"])
    assert m.get_kind() == ColumnMappingKind.SUB_CLASS_OF
    assert m.valid("thing [EX:0000001]")
    assert m.get_value(" thing [EX:0000001] ") == UnresolvedTermIdentifier("EX:0000001", "thing")
    assert m.get_value("thing") == UnresolvedTermIdentifier(None, "thing")
    assert not m.valid("[EX:1]")


def test_term_mapping_with_separator_and_requirements():
    m = TermMapping(kind=ColumnMappingKind.DISJOINT_WITH, columns=["Disjoint"], separator=";")
    assert m.get_value("a [EX:1]; b ;") == [
        UnresolvedTermIdentifier("EX:1", "a"),
        UnresolvedTermIdentifier(None, "b"),
    ]

    strict = TermMapping(
        kind=ColumnMappingKind.IMPORTED_ID, columns=["IDs"], require_id=True, require_label=True, separator=";"
    )
    assert strict.valid("a [EX:1]; b [EX:2]")
    assert not strict.valid("a [EX:1]; b")


def test_choice_mapping():
    m = ChoiceColumnMapping(kind=ColumnMappingKind.RELATION_TYPE, columns=["Relationship type"], choices=["A"])
    assert m.valid(" A ")
    assert not m.valid("Nope")


def test_prefix_mapping():
    m = PrefixColumnMapping(columns=["Prefix"], separator=";")
    assert m.valid('"EX: http://example.org/EX_"; "BFO: http://purl.obolibrary.org/obo/BFO_"')
    assert m.get_value('"EX: http://example.org/EX_"; "BFO: http://purl.obolibrary.org/obo/BFO_"') == [
        ("EX", "http://example.org/EX_"),
        ("BFO", "http://purl.obolibrary.org/obo/BFO_"),
    ]
    assert not m.valid("EX: http://example.org/EX_")


def test_iri_mapping():
    m = IRIMapping(kind=ColumnMappingKind.ONTOLOGY_IRI, columns=["IRI"])
    assert m.valid("http://purl.obolibrary.org/obo/bfo.owl")
    assert not m.valid("bfo.owl")


def test_relation_mapping_values_depend_on_property_type():
    ann = DEFAULT_SCHEMA.get_mapping("f", "Synonyms")
    assert isinstance(ann, RelationColumnMapping)
    assert ann.get_value("a; b") == [(SYNONYM, "a"), (SYNONYM, "b")]

    obj = DEFAULT_SCHEMA.get_mapping("f", "REL 'has part'")
    assert isinstance(obj, RelationColumnMapping)
    assert obj.property_type == OWLPropertyType.ObjectProperty
    values = obj.get_value("wheel; door")
    assert [v for _, v in values] == [UnresolvedTermIdentifier(label="wheel"), UnresolvedTermIdentifier(label="door")]
    assert all(r.label == "has part" for r, _ in values)


def test_pattern_relation_mapping_fills_in_match_groups():
    m = RelationColumnMapping(
        pattern=re.compile(r"REL '([^']+)' \[(\w+:\d+)\]"), relation=RelationRef(id="{2}", label="{1}")
    )

    mapping = m.for_column("sheet.xlsx", "REL 'has part' [EX:9]", m.match("REL 'has part' [EX:9]"))  # type: ignore[arg-type]

    assert (mapping.relation.id, mapping.relation.label) == ("EX:9", "has part")
    assert mapping.get_name() == "REL 'has part' [EX:9]"
    relation = mapping.as_unresolved_relation()
    assert (relation.id, relation.label, relation.origin) == ("EX:9", "has part", ("sheet.xlsx", 0))
    assert m.relation.label == "{1}"  # the schema's mapping is left untouched


def test_pattern_must_match_whole_header():
    assert DEFAULT_SCHEMA.get_mapping("f", "REL 'has part' (old)") is None


def test_mapping_needs_columns_or_pattern():
    with pytest.raises(ValidationError, match="needs `columns` or a `pattern`"):
        SimpleColumnMapping(kind=ColumnMappingKind.ID)


# --- Schema -------------------------------------------------------------------


@pytest.mark.parametrize(
    "header,kind",
    [
        ("ID", ColumnMappingKind.ID),
        ("Label", ColumnMappingKind.LABEL),
        ("Parent", ColumnMappingKind.SUB_CLASS_OF),
        ("Definition", ColumnMappingKind.RELATION),
        ("ANN 'editor note'", ColumnMappingKind.RELATION),
    ],
)
def test_default_schema_mappings(header, kind):
    mapping = DEFAULT_SCHEMA.get_mapping("f", header)
    assert mapping is not None and mapping.get_kind() == kind
    assert mapping.get_name() == header


def test_default_schema_ignored_and_unknown_columns():
    assert DEFAULT_SCHEMA.is_ignored("Curator")
    assert DEFAULT_SCHEMA.get_mapping("f", "Curator") is None
    assert DEFAULT_SCHEMA.get_mapping("f", "REL 'aggregate of'") is None  # ignored before the REL pattern applies
    assert not DEFAULT_SCHEMA.is_ignored("Something else")
    assert DEFAULT_SCHEMA.get_mapping("f", "Something else") is None


def test_default_schema_internal_relations():
    mapping = DEFAULT_SCHEMA.get_mapping("f", "Informal definition")
    assert isinstance(mapping, RelationColumnMapping)
    assert mapping.property_type == OWLPropertyType.Internal
    assert mapping.relation.id is None


def test_default_import_schema_mappings():
    assert DEFAULT_IMPORT_SCHEMA.get_mapping("f", "Ontology ID").get_kind() == ColumnMappingKind.ONTOLOGY_ID  # type: ignore[union-attr]
    assert DEFAULT_IMPORT_SCHEMA.get_mapping("f", "IRI").get_kind() == ColumnMappingKind.ONTOLOGY_IRI  # type: ignore[union-attr]
    assert DEFAULT_IMPORT_SCHEMA.get_mapping("f", "IDs").get_kind() == ColumnMappingKind.IMPORTED_ID  # type: ignore[union-attr]


CUSTOM_SCHEMA = {
    "extends": "default",
    "ignored": ["Notes", "Curator"],
    "mappings": [
        {"type": "label", "columns": ["Term name"]},
        {"type": "plain", "kind": "IGNORE", "columns": ["Curator"]},
        {"type": "term", "kind": "DISJOINT_WITH", "columns": ["Disjoint classes"], "separator": "|"},
        {"type": "relation", "columns": ["Source"], "relation": {"id": "EX:1", "label": "source"}},
    ],
}


def test_schema_from_json():
    schema = Schema.model_validate(CUSTOM_SCHEMA)

    assert [type(m) for m in schema.mappings] == [LabelMapping, SimpleColumnMapping, TermMapping, RelationColumnMapping]
    assert schema.mappings[2].get_kind() == ColumnMappingKind.DISJOINT_WITH
    assert Schema.model_validate_json(schema.model_dump_json()) == schema
    assert Schema.model_validate_json(DEFAULT_SCHEMA.model_dump_json()) == DEFAULT_SCHEMA


@pytest.mark.parametrize(
    "mapping,error",
    [
        ({"type": "nope", "columns": ["A"]}, "does not match any of the expected tags"),
        ({"type": "term", "kind": "NOPE", "columns": ["A"]}, "NOPE"),
        ({"type": "relation", "columns": ["A"]}, "relation"),
        ({"type": "plain", "kind": "ID", "pattern": "("}, "pattern"),
    ],
)
def test_schema_from_json_rejects_invalid_mappings(mapping, error):
    with pytest.raises(ValidationError, match=error):
        Schema.model_validate({"mappings": [mapping]})


def test_resolve_schema_extends_parent():
    schemas = {**BUILTIN_SCHEMAS, "custom": Schema.model_validate(CUSTOM_SCHEMA)}

    schema = resolve_schema("custom", schemas)

    assert schema.get_mapping("f", "Term name").get_kind() == ColumnMappingKind.LABEL  # type: ignore[union-attr]
    assert schema.get_mapping("f", "Label").get_kind() == ColumnMappingKind.LABEL  # type: ignore[union-attr]  # inherited
    disjoint = schema.get_mapping("f", "Disjoint classes")
    assert isinstance(disjoint, TermMapping) and disjoint.separator == "|"  # overrides the parent's mapping
    assert schema.is_ignored("Notes") and schema.is_ignored("Structure")
    assert resolve_schema("default", schemas) is DEFAULT_SCHEMA


def test_resolve_schema_errors():
    schemas = {
        "a": Schema(extends="b"),
        "b": Schema(extends="a"),
        "orphan": Schema(extends="missing"),
    }

    with pytest.raises(ValueError, match="Cyclic spreadsheet schema inheritance: a -> b -> a"):
        resolve_schema("a", schemas)
    with pytest.raises(ValueError, match="Unknown spreadsheet schema 'missing'"):
        resolve_schema("orphan", schemas)
    with pytest.raises(ValueError, match="Unknown spreadsheet schema 'nope'"):
        resolve_schema("nope", schemas)


def test_casts_between_terms_and_identifiers():
    from ose.schema.Term import Term

    term = make_term(sub_class_of=[termid(id="EX:0", label="parent")])
    assert term.assert_resolved_identifier() == TermIdentifier("EX:1", "thing")
    resolved = term._assert_cast(Term)
    assert type(resolved) is Term and resolved.sub_class_of == [TermIdentifier("EX:0", "parent")]
    with pytest.raises(ValueError, match="origin"):
        make_term(origin=None)._assert_cast(Term)
