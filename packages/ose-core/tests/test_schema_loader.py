"""Tests that the YAML-loaded schema matches the old hardcoded schema behavior."""

import pytest

from ose.model.ColumnMapping import (
    ChoiceColumnMapping,
    ColumnMappingKind,
    IRIMapping,
    LabelMapping,
    ManchesterSyntaxMapping,
    ParentMapping,
    PrefixColumnMapping,
    RelationColumnMapping,
    SimpleColumnMapping,
    TermMapping,
)
from ose.model.Relation import OWLPropertyType
from ose.model.Schema import DEFAULT_SCHEMA, DEFAULT_IMPORT_SCHEMA
from ose.model.TermIdentifier import TermIdentifier


ORIGIN = "test_file.xlsx"


class TestEntitySchemaIgnoredFields:
    def test_curator_ignored(self):
        assert DEFAULT_SCHEMA.is_ignored("Curator")

    def test_reviewer_ignored(self):
        assert DEFAULT_SCHEMA.is_ignored("To be reviewed by")

    def test_reviewer_query_ignored(self):
        assert DEFAULT_SCHEMA.is_ignored("Reviewer query")

    def test_bfo_entity_ignored(self):
        assert DEFAULT_SCHEMA.is_ignored("BFO entity")

    def test_structure_ignored(self):
        assert DEFAULT_SCHEMA.is_ignored("Structure")

    def test_non_ignored_not_ignored(self):
        assert not DEFAULT_SCHEMA.is_ignored("ID")


class TestEntitySchemaExplicitlyIgnoredColumns:
    @pytest.mark.parametrize("name", ["REL 'aggregate of'", "Aggregate", "Type"])
    def test_explicitly_ignored(self, name):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert mapping is not None
        assert isinstance(mapping, SimpleColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.IGNORE


class TestEntitySchemaId:
    @pytest.mark.parametrize("name", ["ID", "BCIO_ID"])
    def test_id_mapping(self, name):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert mapping is not None
        assert isinstance(mapping, SimpleColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.ID


class TestEntitySchemaLabel:
    @pytest.mark.parametrize("name", ["Name", "Label", "Label (synonym)", "Relationship"])
    def test_label_mapping(self, name):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert mapping is not None
        assert isinstance(mapping, LabelMapping)
        assert mapping.get_kind() == ColumnMappingKind.LABEL


class TestEntitySchemaParent:
    @pytest.mark.parametrize("name", ["Parent", "Parent class/ BFO class"])
    def test_sub_class_of(self, name):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert mapping is not None
        assert isinstance(mapping, ParentMapping)
        assert mapping.get_kind() == ColumnMappingKind.SUB_CLASS_OF

    def test_sub_property_of(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Parent relationship")
        assert mapping is not None
        assert isinstance(mapping, ParentMapping)
        assert mapping.get_kind() == ColumnMappingKind.SUB_PROPERTY_OF


class TestEntitySchemaEquivalent:
    @pytest.mark.parametrize("name", ["Logical definition", "Logical Definition"])
    def test_equivalent_class_manchester(self, name):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert mapping is not None
        assert isinstance(mapping, ManchesterSyntaxMapping)
        assert mapping.get_kind() == ColumnMappingKind.EQUIVALENT_TO

    def test_equivalent_property(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Equivalent to relationship")
        assert mapping is not None
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.EQUIVALENT_TO


class TestEntitySchemaTermMappings:
    def test_inverse_of(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Inverse of")
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.INVERSE_OF

    def test_disjoint_with(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Disjoint classes")
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.DISJOINT_WITH
        assert mapping.separator == ";"

    def test_domain(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Domain")
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.DOMAIN

    def test_range(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Range")
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.RANGE


class TestEntitySchemaEntityType:
    def test_relationship_type(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Relationship type")
        assert isinstance(mapping, ChoiceColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.RELATION_TYPE
        assert "ObjectProperty" in mapping.choices
        assert "AnnotationProperty" in mapping.choices
        assert "Internal" in mapping.choices


class TestEntitySchemaAnnotationRelations:
    @pytest.mark.parametrize("name,expected_id,expected_label", [
        ("Definition", "IAO:0000115", "definition"),
        ("Definition_ID", "rdfs:isDefinedBy", "rdfs:isDefinedBy"),
        ("Definition_Source", "IAO:0000119", "definition source"),
        ("Definition source", "IAO:0000119", "definition source"),
        ("Definition Source", "IAO:0000119", "definition source"),
        ("Examples", "IAO:0000112", "example of usage"),
        ("Examples of usage", "IAO:0000112", "example of usage"),
        ("Elaboration", "IAO:0000112", "example of usage"),
        ("Curator note", "IAO:0000232", "curator note"),
        ("Synonyms", "IAO:0000118", "alternative label"),
        ("Comment", "rdfs:comment", "rdfs:comment"),
        ("Curation status", "IAO:0000114", "has curation status"),
        ("LSR no.", "GMHOR:0000001", "LSR no"),
        ("Informal label for repository", "GMHOR:0000002", "informal label"),
    ])
    def test_annotation_relation(self, name, expected_id, expected_label):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert isinstance(mapping, RelationColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.RELATION
        relation = mapping.get_relation()
        assert relation.id == expected_id
        assert relation.label == expected_label
        assert relation.owl_property_type == OWLPropertyType.AnnotationProperty

    def test_synonyms_separator(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Synonyms")
        assert isinstance(mapping, RelationColumnMapping)
        assert mapping.separator == ";"

    def test_lsr_separator(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "LSR no.")
        assert isinstance(mapping, RelationColumnMapping)
        assert mapping.separator == ";"


class TestEntitySchemaPatternColumns:
    def test_rel_pattern(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "REL 'has part'")
        assert isinstance(mapping, RelationColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.RELATION
        assert mapping.relation.owl_property_type == OWLPropertyType.ObjectProperty
        assert mapping.relation.label == "has part"
        assert mapping.separator == ";"

    def test_ann_pattern(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "ANN 'my note'")
        assert isinstance(mapping, RelationColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.RELATION
        assert mapping.relation.owl_property_type == OWLPropertyType.AnnotationProperty
        assert mapping.relation.label == "my note"

    def test_non_matching_pattern(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "SOMETHING ELSE")
        assert mapping is None


class TestEntitySchemaInternalFields:
    @pytest.mark.parametrize("name,expected_label", [
        ("Informal definition", "informalDefinition"),
        ("Informal Definition", "informalDefinition"),
        ("informal definition", "informalDefinition"),
        ("Sub-ontology", "lowerLevelOntology"),
        ("Subontology", "lowerLevelOntology"),
        ("Fuzzy set", "fuzzySet"),
        ("Why fuzzy", "fuzzyExplanation"),
        ("Cross reference", "crossReference"),
        ("Cross-reference", "crossReference"),
        ("Ontology section", "ontologySection"),
        ("E-CigO", "eCigO"),
        ("AO sub-ontology", "addictoSubOntology"),
    ])
    def test_internal_field(self, name, expected_label):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, name)
        assert isinstance(mapping, RelationColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.RELATION
        assert mapping.relation.owl_property_type == OWLPropertyType.Internal
        assert mapping.relation.label == expected_label


class TestImportSchema:
    def test_ontology_id(self):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, "Ontology ID")
        assert isinstance(mapping, SimpleColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.ONTOLOGY_ID

    @pytest.mark.parametrize("name", ["PURL", "IRI"])
    def test_ontology_iri(self, name):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, name)
        assert isinstance(mapping, IRIMapping)
        assert mapping.get_kind() == ColumnMappingKind.ONTOLOGY_IRI

    @pytest.mark.parametrize("name", ["Exclude", "Excluding", "Excluded", "Remove"])
    def test_excluded_import_id(self, name):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, name)
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.EXCLUDED_IMPORT_ID
        assert mapping.separator == ";"
        assert mapping.require_id is True
        assert mapping.require_label is True

    def test_root_id(self):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, "ROOT_ID")
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.ROOT_ID
        assert mapping.require_id is True
        assert mapping.require_label is True

    def test_version_iri(self):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, "VERSION")
        assert isinstance(mapping, IRIMapping)
        assert mapping.get_kind() == ColumnMappingKind.VERSION_IRI

    def test_imported_ids(self):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, "IDs")
        assert isinstance(mapping, TermMapping)
        assert mapping.get_kind() == ColumnMappingKind.IMPORTED_ID
        assert mapping.separator == ";"
        assert mapping.require_id is True
        assert mapping.require_label is True

    def test_intermediates(self):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, "Intermediates")
        assert isinstance(mapping, SimpleColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.PLAIN

    def test_prefix(self):
        mapping = DEFAULT_IMPORT_SCHEMA.get_mapping(ORIGIN, "Prefix")
        assert isinstance(mapping, PrefixColumnMapping)
        assert mapping.get_kind() == ColumnMappingKind.PREFIX
        assert mapping.separator == ";"


class TestEntitySchemaValueBehavior:
    """Test that mapped columns correctly parse values, matching old behavior."""

    def test_parent_parses_label_with_id(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Parent")
        assert isinstance(mapping, ParentMapping)
        result = mapping.get_value("Some Term [ABC:123]")
        assert result == TermIdentifier(id="ABC:123", label="Some Term")

    def test_parent_parses_label_only(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Parent")
        result = mapping.get_value("Some Term")
        assert result == TermIdentifier(id=None, label="Some Term")

    def test_label_parses_name(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Label")
        assert isinstance(mapping, LabelMapping)
        assert mapping.get_value("My Term") == "My Term"

    def test_disjoint_parses_multiple(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "Disjoint classes")
        assert isinstance(mapping, TermMapping)
        result = mapping.get_value("Term A [X:1]; Term B [X:2]")
        assert len(result) == 2
        assert result[0] == TermIdentifier(id="X:1", label="Term A")
        assert result[1] == TermIdentifier(id="X:2", label="Term B")

    def test_rel_pattern_value_as_term_identifier(self):
        mapping = DEFAULT_SCHEMA.get_mapping(ORIGIN, "REL 'has part'")
        assert isinstance(mapping, RelationColumnMapping)
        result = mapping.get_value("some value; other value")
        assert len(result) == 2
        # Object property values are wrapped as TermIdentifier
        assert result[0][1] == TermIdentifier(label="some value")
        assert result[1][1] == TermIdentifier(label="other value")
