import csv
from typing import Any

import openpyxl
import pyhornedowl as ho
import pyhornedowl.model as hom

PREFIXES = {
    "EX": "http://example.org/EX_",
    "IAO": "http://purl.obolibrary.org/obo/IAO_",
    "BFO": "http://purl.obolibrary.org/obo/BFO_",
}
RDFS_LABEL = "http://www.w3.org/2000/01/rdf-schema#label"

TERM_HEADER = ["ID", "Label", "Parent", "Definition", "Curation status"]


def write_xlsx(path, rows: list[list[Any]]) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    for row in rows:
        ws.append(row)
    wb.save(path)
    return str(path)


def write_csv(path, rows: list[list[str]]) -> str:
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    return str(path)


def project_data(**overrides) -> dict[str, Any]:
    """Raw (JSON-like) project configuration with one external file and two dependent class files."""
    data: dict[str, Any] = {
        "short_name": "EX",
        "full_name": "Example Ontology",
        "iri_prefix": "http://example.org/",
        "short_repository_name": "ex",
        "full_repository_name": "example/ex",
        "prefixes": PREFIXES,
        "external": {"sources": ["external.xlsx"], "target": "external.owl"},
        "files": {
            "upper": {"sources": ["upper.xlsx"], "target": "upper.owl"},
            "lower": {"sources": ["lower.xlsx"], "target": "lower.owl", "needs": ["upper"]},
        },
        "build_configurations": [{"name": "default", "stages": [{"name": "MERGE"}]}],
    }
    data.update(overrides)
    return data


def write_owl(
    path, classes: dict[str, str | None], parents: dict[str, str] | None = None, iri: str | None = None
) -> str:
    """Write an OWL file with the given classes (IRI -> label) and parents (child IRI -> parent IRI)."""
    o = ho.PyIndexedOntology()
    if iri is not None:
        o.add_component(hom.OntologyID(o.iri(iri), None))
    label = o.annotation_property(RDFS_LABEL)
    for c, name in classes.items():
        o.declare_class(c)
        if name is not None:
            o.add_component(hom.AnnotationAssertion(o.iri(c), hom.Annotation(label, hom.SimpleLiteral(name))))
    for child, parent in (parents or {}).items():
        o.add_component(hom.SubClassOf(o.class_(child), o.class_(parent)))
    o.save_to_file(str(path))
    return str(path)
