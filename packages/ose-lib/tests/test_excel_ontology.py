import pyhornedowl as ho
import pyhornedowl.model as hom

from helpers import PREFIXES, TERM_HEADER, project_data, write_csv, write_xlsx
from ose import constants
from ose.ontology.ExcelOntology import ExcelOntology
from ose.result import is_err, is_successful
from ose.schema import Schema

IRI = "http://example.org/ex.owl"
EX = "http://example.org/EX_"
IAO_DEFINITION = "http://purl.obolibrary.org/obo/IAO_0000115"

ROWS = [
    ["EX:0000001", "thing", None, "A thing.", "Published"],
    ["EX:0000002", "object", "thing", "An object.", "Published"],
    ["EX:0000003", "part", "object [EX:0000002]", "A part.", "Published"],
]


def ontology(rows=ROWS, header=TERM_HEADER, **kwargs) -> ExcelOntology:
    o = ExcelOntology(IRI, **kwargs)
    assert is_successful(o.add_terms_from_list(rows, header, origin="terms.xlsx"))
    return o


def types(messages) -> list[str]:
    return [m["type"] for m in messages]


# --- Parsing ------------------------------------------------------------------


def test_add_terms_from_list_parses_and_resolves_terms():
    o = ontology()
    assert [t.id for t in o.terms()] == ["EX:0000001", "EX:0000003"]  # "object" has an unresolved parent

    assert is_successful(o.resolve())

    assert [t.id for t in o.terms()] == ["EX:0000001", "EX:0000002", "EX:0000003"]
    obj = o.term_by_id("EX:0000002")
    assert obj is not None
    assert obj.origin == ("terms.xlsx", 3)
    assert obj.definition() == "An object."
    assert [(p.id, p.label) for p in obj.sub_class_of] == [("EX:0000001", "thing")]
    assert o.find_term_id("part") == "EX:0000003"
    assert o.find_term_label("EX:0000003") == "part"
    assert o.term_by_label("thing") == o.term_by_id("EX:0000001")
    assert o.iri() == IRI


def test_unknown_column_warns():
    o = ExcelOntology(IRI)
    result = o.add_terms_from_list([["EX:1", "thing", "x"]], ["ID", "Label", "Mystery"])

    assert is_successful(result)
    assert types(result.log.warnings) == ["unknown-column"]
    assert result.log.warnings[0]["column"] == "Mystery"


def test_ignored_column_does_not_warn():
    result = ExcelOntology(IRI).add_terms_from_list([["EX:1", "thing", "me"]], ["ID", "Label", "Curator"])
    assert result.log.warnings == []


def test_invalid_value_is_an_error():
    o = ExcelOntology(IRI)
    result = o.add_terms_from_list([["EX:1", "thing", "[EX:2]"]], ["ID", "Label", "Parent"], origin="t.xlsx")

    assert is_err(result)
    assert types(result.log.errors) == ["invalid-value"]
    assert result.log.errors[0]["row"] == 2
    assert result.log.errors[0]["column"] == "Parent"


def test_empty_row_is_skipped_with_warning():
    o = ExcelOntology(IRI)
    result = o.add_terms_from_list([[None, None, None, None, None]], TERM_HEADER)

    assert types(result.log.warnings) == ["incomplete-term"]
    o.resolve()
    assert o.terms() == []


def test_curation_status_filtering():
    rows = ROWS + [
        ["EX:0000004", "old", "thing", "Old.", "Obsolete"],
        ["EX:0000005", "gone", "thing", "Gone.", "Discarded"],
    ]
    o = ontology(rows, discard_terms_with_status=["discarded"])
    o.resolve()

    assert "EX:0000004" not in [t.id for t in o.terms()]
    assert o.find_term_id("old") == "EX:0000004"  # ignored terms remain referencable
    assert o.find_term_id("gone") is None  # discarded terms are not parsed at all


def test_add_terms_from_excel_reads_sheet_and_skips_blank_cells(tmp_path):
    file = write_xlsx(tmp_path / "terms.xlsx", [TERM_HEADER, *ROWS])
    o = ExcelOntology(IRI)

    result = o.add_terms_from_excel("terms.xlsx", file)
    assert is_successful(result)
    o.resolve()

    thing = o.term_by_id("EX:0000001")
    assert thing is not None
    assert thing.origin == ("terms.xlsx", 2)
    assert thing.sub_class_of == []  # blank "Parent" cell must not become a parent called "None"
    assert [t.id for t in o.terms()] == ["EX:0000001", "EX:0000002", "EX:0000003"]


def test_add_terms_from_excel_accepts_bytes(tmp_path):
    file = write_xlsx(tmp_path / "terms.xlsx", [TERM_HEADER, *ROWS])
    o = ExcelOntology(IRI)
    with open(file, "rb") as f:
        assert is_successful(o.add_terms_from_excel("terms.xlsx", f.read()))
    assert o.find_term_id("part") == "EX:0000003"


def test_excel_blank_header_preserves_column_alignment(tmp_path):
    file = write_xlsx(
        tmp_path / "terms.xlsx",
        [["ID", None, "Label", "Parent"], ["EX:1", "ignored", "thing", None]],
    )
    o = ExcelOntology(IRI)

    assert is_successful(o.add_terms_from_excel("terms.xlsx", file))
    assert o.find_term_id("thing") == "EX:1"


def test_excel_empty_sheet_is_handled(tmp_path):
    file = write_xlsx(tmp_path / "empty.xlsx", [])
    result = ExcelOntology(IRI).add_terms_from_excel("empty.xlsx", file)

    assert is_successful(result)


# --- Relations ----------------------------------------------------------------

RELATION_HEADER = ["ID", "Relationship", "Domain", "Range", "Relationship type"]
CAR = ["EX:0000004", "car", "object", "A car.", "Published", "part"]


def test_relations_from_excel_and_their_use_in_terms(tmp_path):
    relations = write_xlsx(
        tmp_path / "relations.xlsx",
        [RELATION_HEADER, ["EX:0000010", "has part", "object", "part [EX:0000003]", "ObjectProperty"]],
    )
    o = ontology([*ROWS, CAR], TERM_HEADER + ["REL 'has part'"])
    assert is_successful(o.add_relations_from_excel("relations.xlsx", relations))

    assert is_successful(o.resolve())

    [has_part] = o.relations()
    assert (has_part.id, has_part.label) == ("EX:0000010", "has part")
    assert has_part.origin == ("relations.xlsx", 2)
    assert has_part.domain is not None and has_part.domain.id == "EX:0000002"
    assert has_part.range is not None and has_part.range.id == "EX:0000003"

    car = o.term_by_id("EX:0000004")
    assert car is not None
    rel, value = next((r, v) for r, v in car.relations if r.label == "has part")
    assert rel.id == "EX:0000010"
    assert (value.id, value.label) == ("EX:0000003", "part")

    assert "unknown-relation" not in types(o.validate().log.errors)

    exported = [[cell.value for cell in row] for row in o.to_excel().active.rows]
    relation_column = exported[0].index("REL 'has part'")
    car_row = next(row for row in exported[1:] if row[0] == "EX:0000004")
    assert car_row[relation_column] == "part [EX:0000003]"


def test_equivalent_and_inverse_relations_resolve_to_relations(tmp_path):
    relations = write_xlsx(
        tmp_path / "relations.xlsx",
        [
            ["ID", "Relationship", "Equivalent to relationship", "Inverse of"],
            ["EX:10", "has part", "part of", None],
            ["EX:11", "part of", None, "has part"],
        ],
    )
    o = ExcelOntology(IRI)
    assert is_successful(o.add_relations_from_excel("relations.xlsx", relations))

    assert is_successful(o.resolve())
    has_part, part_of = o.relations()
    assert [(r.id, r.label) for r in has_part.equivalent_relations] == [("EX:11", "part of")]
    assert [(r.id, r.label) for r in part_of.inverse_of] == [("EX:10", "has part")]


def test_relation_resolution_matches_id_when_used_label_is_none():
    from ose.schema import OWLPropertyType, UnresolvedRelation

    o = ExcelOntology(IRI)
    o._relations.append(
        UnresolvedRelation(
            id="EX:10",
            label="has part",
            owl_property_type=OWLPropertyType.ObjectProperty,
            origin=("relations.xlsx", 2),
        )
    )
    o._used_relations.add(
        UnresolvedRelation(id="EX:10", owl_property_type=OWLPropertyType.ObjectProperty, origin=("terms.xlsx", 1))
    )

    assert is_successful(o.resolve())
    [used] = o.used_relations()
    assert (used.id, used.label) == ("EX:10", "has part")


def test_to_owl_relation_annotation_uses_relation_as_subject(tmp_path):
    schema = Schema.model_validate(
        {
            "mappings": [
                {"type": "plain", "kind": "ID", "columns": ["ID"]},
                {"type": "label", "columns": ["Relationship"]},
                {
                    "type": "relation",
                    "columns": ["Note"],
                    "relation": {"id": "EX:20", "label": "note"},
                },
            ]
        }
    )
    relations = write_xlsx(
        tmp_path / "relations.xlsx",
        [["ID", "Relationship", "Note"], ["EX:10", "has part", "note value"]],
    )
    o = ExcelOntology(IRI)
    assert is_successful(o.add_relations_from_excel("relations.xlsx", relations, schema))
    assert is_successful(o.resolve())

    result = o.to_owl(PREFIXES)
    assert is_successful(result)
    out = str(tmp_path / "out.owl")
    result.value.save_to_file(out)
    owl = ho.open_ontology(out)
    assert owl.get_annotation(EX + "10", EX + "20") == "note value"


def test_undefined_relation_column_is_reported():
    o = ontology([*ROWS, CAR], TERM_HEADER + ["REL 'has part'"])
    o.resolve()

    assert "unknown-relation" in types(o.validate().log.errors)


# --- Imports ------------------------------------------------------------------


def test_add_imported_terms(tmp_path):
    file = write_xlsx(
        tmp_path / "imports.xlsx",
        [
            ["Ontology ID", "IRI", "ROOT_ID", "IDs", "Intermediates", "Prefix"],
            [
                "BFO",
                "http://purl.obolibrary.org/obo/bfo.owl",
                "entity [BFO:0000001]",
                "entity [BFO:0000001]; process [BFO:0000015]",
                "minimal",
                '"BFO: http://purl.obolibrary.org/obo/BFO_"',
            ],
        ],
    )
    o = ExcelOntology(IRI)

    assert is_successful(o.add_imported_terms("imports.xlsx", file))

    [imp] = o.imports()
    assert imp.id == "BFO"
    assert imp.iri == "http://purl.obolibrary.org/obo/bfo.owl"
    assert imp.root_id is not None and imp.root_id.id == "BFO:0000001"
    assert imp.intermediates == "minimal"
    assert imp.prefixes == [("BFO", "http://purl.obolibrary.org/obo/BFO_")]
    assert [(t.id, t.label) for t in o.imported_terms()] == [("BFO:0000001", "entity"), ("BFO:0000015", "process")]

    o.add_terms_from_list([["EX:1", "running", "process"]], ["ID", "Label", "Parent"])
    o.resolve()
    running = o.term_by_id("EX:1")
    assert running is not None and running.sub_class_of[0].id == "BFO:0000015"


def test_import_without_ontology_id_fails(tmp_path):
    file = write_xlsx(
        tmp_path / "imports.xlsx",
        [["Ontology ID", "IRI"], [None, "http://example.org/import.owl"]],
    )
    result = ExcelOntology(IRI).add_imported_terms("imports.xlsx", file)

    assert is_err(result)
    assert types(result.log.errors) == ["missing-ontology-id"]


def test_renaming_scope_all_updates_local_and_imported_terms(tmp_path):
    imports = write_xlsx(
        tmp_path / "imports.xlsx",
        [["Ontology ID", "IRI", "IDs"], ["EXT", "http://example.org/ext.owl", "thing [EX:1]"]],
    )
    renames = write_csv(tmp_path / "renames.csv", [["ID", "NEW LABEL"], ["EX:1", "renamed"]])
    o = ExcelOntology(IRI)
    o.add_terms_from_list([["EX:1", "thing"]], ["ID", "Label"])
    assert is_successful(o.add_imported_terms("imports.xlsx", imports))

    o.apply_renamings(renames, scope="all")

    assert o.find_term_label("EX:1") == "renamed"
    assert [(term.id, term.label) for term in o.imported_terms()] == [("EX:1", "renamed")]


def test_import_other_excel_ontology_resolves_references():
    upper = ontology()
    upper.resolve()

    lower = ExcelOntology("http://example.org/lower.owl")
    lower.add_terms_from_list([["EX:0000100", "wheel", "part"]], ["ID", "Label", "Parent"])
    assert is_successful(lower.import_other_excel_ontology(upper))
    lower.resolve()

    assert [i.id for i in lower.imports()] == [IRI]
    wheel = lower.term_by_id("EX:0000100")
    assert wheel is not None and wheel.sub_class_of[0].id == "EX:0000003"
    assert lower.validate().log.errors == []


def test_from_project_file_resolves_rename_and_parent_paths(tmp_path):
    from ose.ontology.loading import from_project_file
    from ose.project import Project

    write_xlsx(tmp_path / "upper.xlsx", [TERM_HEADER, *ROWS])
    write_csv(tmp_path / "rename.csv", [["ID", "NEW LABEL"], ["EX:0000002", "item"]])
    write_csv(tmp_path / "parents.csv", [["ID", "NEW PARENT ID"], ["EX:0000003", "EX:0000001"]])
    data = project_data()
    data["files"]["upper"].update(renameTermFile="rename.csv", addParentsFile="parents.csv")
    project = Project.model_validate(data)

    result = from_project_file(project.files["upper"], project, str(tmp_path))
    assert is_successful(result)
    result.value.resolve()
    assert result.value.find_term_label("EX:0000002") == "item"
    part = result.value.term_by_id("EX:0000003")
    assert part is not None and "EX:0000001" in [parent.id for parent in part.sub_class_of]


def test_merge_with_combines_terms_and_imports():
    a = ontology(ROWS[:1])
    b = ontology(ROWS[1:])
    b.import_other_excel_ontology(ExcelOntology("http://example.org/other.owl"))

    a.merge_with(b)
    a.resolve()

    assert [t.id for t in a.terms()] == ["EX:0000001", "EX:0000002", "EX:0000003"]
    assert [i.id for i in a.imports()] == ["http://example.org/other.owl"]


# --- Modifications ------------------------------------------------------------


def test_apply_renamings(tmp_path):
    file = write_csv(tmp_path / "rename.csv", [["ID", "NEW LABEL"], ["EX:0000002", "item"]])
    o = ontology()
    o.apply_renamings(file)
    o.resolve()

    assert o.find_term_label("EX:0000002") == "item"


def test_apply_new_parents(tmp_path):
    file = write_csv(
        tmp_path / "parents.csv",
        [["ID", "NEW PARENT ID", "TYPE"], ["EX:0000003", "EX:0000001", "class"]],
    )
    o = ontology()
    o.apply_new_parents(file)
    o.resolve()

    part = o.term_by_id("EX:0000003")
    assert part is not None and [p.id for p in part.sub_class_of] == ["EX:0000002", "EX:0000001"]


def test_remove_duplicates():
    o = ontology(ROWS + [ROWS[1]])
    assert o.remove_duplicates() == 1
    o.resolve()
    assert sorted(t.id for t in o.terms()) == ["EX:0000001", "EX:0000002", "EX:0000003"]


def test_validate_and_remove_duplicates_tolerate_missing_labels():
    o = ExcelOntology(IRI)
    assert is_successful(o.add_terms_from_list([["EX:1", None]], ["ID", "Label"]))

    result = o.validate(only=["missing-label"])
    assert is_err(result)
    assert types(result.log.errors) == ["missing-label"]
    assert o.remove_duplicates() == 0


def test_csv_modifications_skip_blank_rows_and_accept_two_column_parents(tmp_path):
    parent_file = write_csv(
        tmp_path / "parents.csv",
        [["ID", "NEW PARENT ID"], [], ["EX:0000003", "EX:0000001"]],
    )
    rename_file = write_csv(
        tmp_path / "rename.csv",
        [["ID", "NEW LABEL"], [], ["EX:0000002", "item"]],
    )
    o = ontology()

    o.apply_new_parents(parent_file)
    o.apply_renamings(rename_file)
    o.resolve()

    assert o.find_term_label("EX:0000002") == "item"
    part = o.term_by_id("EX:0000003")
    assert part is not None and "EX:0000001" in [parent.id for parent in part.sub_class_of]


# --- Validation ---------------------------------------------------------------


def test_valid_ontology_only_reports_missing_root_parent():
    o = ontology()
    o.resolve()

    assert types(o.validate().log.errors) == ["no-parent"]
    assert o.validate(exclude=["no-parent"]).log.errors == []


def test_validate_reports_unknown_parent():
    o = ontology([*ROWS, ["EX:0000004", "orphan", "nonexistent", "Orphan.", "Published"]])
    o.resolve()

    errors = o.validate(only=["unknown-parent"]).log.errors
    assert types(errors) == ["unknown-parent"]
    assert errors[0]["row"] == 5


def test_validate_reports_duplicates():
    o = ontology([*ROWS, ["EX:0000002", "other object", "thing", "Different.", "Published"]])
    o.resolve()

    errors = o.validate(only=["duplicate"]).log.errors
    assert types(errors) == ["duplicate"]
    assert errors[0]["duplicate_value"] == "EX:0000002"


def test_validate_reports_duplicate_labels_with_field_label():
    o = ontology([["EX:1", "same", None, "", ""], ["EX:2", "same", None, "", ""]])
    errors = o.validate(only=["duplicate"]).log.errors

    assert len(errors) == 1
    assert errors[0]["duplicate_field"] == "label"
    assert errors[0]["duplicate_value"] == "same"


def test_validate_reports_ignored_parent():
    o = ontology(
        [*ROWS, ["EX:0000004", "old", "thing", "Old.", "Obsolete"], ["EX:5", "new", "old", "New.", "Published"]]
    )
    o.resolve()

    assert types(o.validate(only=["ignored-parent"]).log.errors) == ["ignored-parent"]


def test_validate_reports_external_terms_missing_from_imports():
    o = ontology([*ROWS, ["BFO:0000001", "entity", "thing", "Entity.", "External"]])
    o.resolve()

    assert types(o.validate(only=["missing-import"]).log.warnings) == ["missing-import"]


# --- OWL ----------------------------------------------------------------------


def test_to_owl(tmp_path):
    o = ontology()
    o.resolve()

    result = o.to_owl(PREFIXES)
    assert is_successful(result)
    out = str(tmp_path / "out.owl")
    result.value.save_to_file(out)

    owl = ho.open_ontology(out)
    assert owl.get_classes() >= {EX + "0000001", EX + "0000002", EX + "0000003"}
    assert owl.get_annotation(EX + "0000002", constants.RDFS_LABEL) == "object"
    assert owl.get_annotation(EX + "0000002", IAO_DEFINITION) == "An object."
    assert owl.get_superclasses(EX + "0000003") == {EX + "0000002"}


def test_from_owl(tmp_path):
    owl = ho.PyIndexedOntology()
    label = owl.annotation_property(constants.RDFS_LABEL)
    for id, name in [("0000001", "thing"), ("0000002", "object")]:
        owl.declare_class(EX + id)
        owl.add_component(hom.AnnotationAssertion(owl.iri(EX + id), hom.Annotation(label, hom.SimpleLiteral(name))))
    owl.add_component(hom.SubClassOf(owl.class_(EX + "0000002"), owl.class_(EX + "0000001")))
    owl.add_component(hom.DeclareObjectProperty(owl.object_property(EX + "0000010")))
    owl.add_component(
        hom.AnnotationAssertion(owl.iri(EX + "0000010"), hom.Annotation(label, hom.SimpleLiteral("has part")))
    )
    owl.declare_class(EX + "0000099")  # no label
    file = str(tmp_path / "in.owl")
    owl.save_to_file(file)

    result = ExcelOntology.from_owl(file, PREFIXES)

    assert is_successful(result)
    o = result.value
    obj = o.term_by_id("EX:0000002")
    assert obj is not None and obj.label == "object"
    assert [(p.id, p.label) for p in obj.sub_class_of] == [("EX:0000001", "thing")]
    assert [(r.id, r.label) for r in o.relations()] == [("EX:0000010", "has part")]
    assert "unknown-label" in types(result.log.warnings)


def test_to_excel():
    o = ontology()
    o.resolve()

    rows = [[c.value for c in row] for row in o.to_excel(include_origin=True).active.rows]

    assert rows[0][:5] == ["ID", "Label", "Parent", "Disjoint classes", "Logical definition"]
    assert rows[0][-1] == "origin"
    assert rows[3][:3] == ["EX:0000003", "part", "object [EX:0000002]"]
    assert rows[3][-1] == "terms.xlsx:4"


# --- loading.from_project_file ------------------------------------------------
# Imported lazily so the tests above still run if the build models fail to import.


def test_from_project_file(tmp_path):
    from ose.ontology.loading import from_project_file
    from ose.project import Project

    write_xlsx(tmp_path / "upper.xlsx", [TERM_HEADER, *ROWS])
    project = Project.model_validate(project_data())

    result = from_project_file(project.files["upper"], project, str(tmp_path))

    assert is_successful(result)
    assert result.value.iri() == "http://example.org/upper.owl"
    assert result.value.find_term_id("object") == "EX:0000002"


def test_from_project_file_unknown_schema(tmp_path):
    from ose.ontology.loading import from_project_file
    from ose.project import Project

    project = Project.model_validate(project_data())
    project.files["upper"].sources[0].spreadsheet_schema = "missing"

    result = from_project_file(project.files["upper"], project, str(tmp_path))

    assert is_err(result)
    assert types(result.log.errors) == ["schema-not-found"]


def test_from_project_file_with_custom_schema(tmp_path):
    from ose.ontology.loading import from_project_file
    from ose.project import Project

    write_xlsx(tmp_path / "upper.xlsx", [["ID", "Term name", "Parent"], ["EX:0000001", "thing", None]])
    data = project_data(
        spreadsheet_schemas={
            "custom": {"extends": "default", "mappings": [{"type": "label", "columns": ["Term name"]}]}
        }
    )
    data["files"]["upper"]["sources"] = [{"file": "upper.xlsx", "type": "classes", "spreadsheet_schema": "custom"}]
    project = Project.model_validate(data)

    result = from_project_file(project.files["upper"], project, str(tmp_path))

    assert is_successful(result), result.log
    assert result.value.find_term_id("thing") == "EX:0000001"


def test_blank_and_empty_cells_are_skipped():
    o = ExcelOntology(IRI)
    rows = [["EX:1", "thing", None, "  "], ["EX:2", "other", "", ""]]
    assert is_successful(o.add_terms_from_list(rows, ["ID", "Label", "Parent", "Definition"]))
    o.resolve()

    assert [(t.id, t.sub_class_of, t.relations) for t in o.terms()] == [("EX:1", [], []), ("EX:2", [], [])]
