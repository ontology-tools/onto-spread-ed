from typing import List, Optional

from .ColumnMapping import ColumnMappingFactory, ColumnMapping, simple, \
    ColumnMappingKind, singleton, LabelMapping, ParentMapping, ManchesterSyntaxMapping, TermMapping, \
    ChoiceColumnMapping, relation, relation_pattern, internal, PrefixColumnMapping, ignore, IRIMapping
from .Relation import OWLPropertyType
from .TermIdentifier import TermIdentifier


class Schema:
    _mapping_factories: List[ColumnMappingFactory]

    def __init__(self, mapping_factories: List[ColumnMappingFactory],
                 ignored_fields: Optional[List[str]] = None) -> None:
        if ignored_fields is None:
            ignored_fields = []

        self._mapping_factories = mapping_factories
        self._ignored_fields = ignored_fields

    def is_ignored(self, header_name: str) -> bool:
        return header_name in self._ignored_fields

    def get_mapping(self, origin: str, header_name: str) -> Optional[ColumnMapping]:
        if self.is_ignored(header_name):
            return None

        return next(
            iter(m.create_mapping(origin, header_name) for m in self._mapping_factories if m.maps(header_name)), None)


DEFAULT_MAPPINGS = [
    ignore("REL 'aggregate of'"),
    ignore("Aggregate"),
    ignore("Type"),
    simple(["ID", "BCIO_ID"], ColumnMappingKind.ID),
    singleton(["Domain"], TermMapping, kind=ColumnMappingKind.DOMAIN),
    singleton(["Range"], TermMapping, kind=ColumnMappingKind.RANGE),
    singleton(["Name", "Label", "Label (synonym)", "Relationship"], LabelMapping),
    singleton(["Parent", "Parent class/ BFO class"], ParentMapping, kind=ColumnMappingKind.SUB_CLASS_OF),
    singleton(["Parent relationship"], ParentMapping, kind=ColumnMappingKind.SUB_PROPERTY_OF),
    singleton(["Logical definition", "Logical Definition"],
              ManchesterSyntaxMapping, kind=ColumnMappingKind.EQUIVALENT_TO),
    singleton(["Equivalent to relationship"], TermMapping, kind=ColumnMappingKind.EQUIVALENT_TO),
    singleton(["Inverse of"], TermMapping, kind=ColumnMappingKind.INVERSE_OF),
    singleton(["Disjoint classes"], TermMapping, kind=ColumnMappingKind.DISJOINT_WITH, separator=";"),
    singleton(["Relationship type"], ChoiceColumnMapping, kind=ColumnMappingKind.RELATION_TYPE,
              choices=[t.name for t in OWLPropertyType]),
    relation(["LSR no."], TermIdentifier(id="GMHOR:0000001", label="LSR no"), separator=";"),
    relation(["Informal label for repository"], TermIdentifier(id="GMHOR:0000002", label="informal label"), separator=";"),
    relation(["Definition"], TermIdentifier(id="IAO:0000115", label="definition")),
    relation(["Definition_ID"], TermIdentifier(id="rdfs:isDefinedBy", label="rdfs:isDefinedBy")),
    relation(["Definition_Source", "Definition source", "Definition Source"],
             TermIdentifier(id="IAO:0000119", label="definition source")),
    relation(["Examples", "Examples of usage", "Elaboration"],
             TermIdentifier(id="IAO:0000112", label="example of usage")),
    relation(["Curator note"], TermIdentifier(id="IAO:0000232", label="curator note")),
    relation(["Synonyms"], TermIdentifier(id="IAO:0000118", label="alternative label"), separator=";"),
    relation(["Comment"], TermIdentifier(id="rdfs:comment", label="rdfs:comment")),
    relation(["Curation status"], TermIdentifier(id="IAO:0000114", label="has curation status")),
    relation_pattern(r"REL '([^']+)'",
                     lambda name, match: TermIdentifier(label=match.group(1)),
                     relation_kind=OWLPropertyType.ObjectProperty, separator=";"),
    relation_pattern(r"ANN '([^']+)'",
                     lambda name, match: TermIdentifier(label=match.group(1)),
                     relation_kind=OWLPropertyType.AnnotationProperty),
    internal(["Informal definition", "Informal Definition", "informal definition"], "informalDefinition"),
    internal(["Sub-ontology", "Subontology"], "lowerLevelOntology"),
    internal(["Fuzzy set"], "fuzzySet"),
    internal(["Why fuzzy"], "fuzzyExplanation"),
    internal(["Cross reference", "Cross-reference"], "crossReference"),
    internal(["Ontology section"], "ontologySection"),
    internal(["E-CigO"], "eCigO"),
    internal(["AO sub-ontology"], "addictoSubOntology")
]
DEFAULT_IGNORED_FIELDS = ["Curator", "To be reviewed by", "Reviewer query", "BFO entity", "Structure"]
DEFAULT_SCHEMA = Schema(DEFAULT_MAPPINGS, DEFAULT_IGNORED_FIELDS)
DEFAULT_IMPORT_SCHEMA = Schema([
    simple(["Ontology ID"], ColumnMappingKind.ONTOLOGY_ID),
    singleton(["PURL", "IRI"], IRIMapping, kind=ColumnMappingKind.ONTOLOGY_IRI),
    singleton(["Exclude", "Excluding", "Excluded", "Remove"], TermMapping, kind=ColumnMappingKind.EXCLUDED_IMPORT_ID,
              separator=";", require_id=True, require_label=True),
    singleton(["ROOT_ID"], TermMapping, kind=ColumnMappingKind.ROOT_ID, require_id=True, require_label=True),
    singleton(["VERSION"], IRIMapping, kind=ColumnMappingKind.VERSION_IRI),
    singleton(["IDs"], TermMapping, kind=ColumnMappingKind.IMPORTED_ID, require_id=True, require_label=True,
              separator=";"),
    simple(["Intermediates"], ColumnMappingKind.PLAIN),
    singleton(["Prefix"], PrefixColumnMapping, separator=";")

])
