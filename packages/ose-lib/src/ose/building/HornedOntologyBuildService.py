from typing import Any, Dict, List, Literal, Tuple

from ose.ontology import ExcelOntology, OntologyImport
from ose.result import ResultContext, Result, with_result_context_method

from ose.building.OntologyBuildService import OntologyBuildService

import pyhornedowl as ho
import pyhornedowl.model as hom


class HornedOntologyBuildService(OntologyBuildService):
    async def merge_imports(
        self,
        imports: List[OntologyImport],
        outfile: str,
        iri: str,
        main_ontology_name: str,
        renamings: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
        new_parents: List[
            Tuple[str, str, Literal["class", "object property", "data_property"]]
        ],
    ) -> Result[Any]:
        raise NotImplementedError

    @with_result_context_method
    async def build_ontology(
        self,
        ctx: ResultContext,
        ontology: ExcelOntology,
        outfile: str,
        prefixes: Dict[str, str] | None,
        dependency_iris: List[str] | None,
        local_ontologies: Dict[str, str],
        iri_prefix: str,
    ) -> ho.PyIndexedOntology:
        missing = [dependency for dependency in dependency_iris or [] if dependency not in local_ontologies]
        if missing:
            ctx.fail(
                type="unknown-dependency",
                msg=f"No local files for the dependencies {', '.join(missing)}",
            )

        result = ctx.unwrap(ontology.to_owl(prefixes if prefixes is not None else {}))
        result.save_to_file(outfile)
        return result

    @with_result_context_method
    async def merge_ontologies(
        self,
        ctx: ResultContext,
        ontologies: List[str],
        outfile: str,
        iri: str,
        version_iri: str,
        annotations: Dict[str, str],
    ) -> ho.PyIndexedOntology:
        o = ho.PyIndexedOntology()
        o.add_component(hom.OntologyID(o.iri(iri), o.iri(version_iri) if version_iri else None))
        
        for path in ontologies:
            try:
                ontology = ho.open_ontology_from_file(path)
            except (OSError, ValueError) as e:
                ctx.fail(type="unreadable-ontology", file=path, msg=str(e))
            for c in ontology.get_components():
                if isinstance(c.component, hom.OntologyID):
                    continue  # keep the merged ontology's own ID
                o.add_component(c.component, c.ann)

        for property_iri, value in annotations.items():
            o.add_component(
                hom.OntologyAnnotation(
                    hom.Annotation(
                        o.annotation_property(property_iri),
                        hom.SimpleLiteral(value),
                    )
                )
            )

        o.save_to_file(outfile)

        return o

    async def collapse_imports(self, file: str) -> Result[Any]:
        raise NotImplementedError
