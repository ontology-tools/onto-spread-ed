from os import path

from ose.project import ProjectFile, Project
from ose.result import ResultContext, with_result_context
from ose.ontology.ExcelOntology import ExcelOntology


@with_result_context
def from_project_file(
    ctx: ResultContext,
    project_file: ProjectFile,
    project: Project,
    working_dir: str | None = None,
) -> ExcelOntology:
    """
    Create an ExcelOntology from a ProjectFile.

    :param project_file: The ProjectFile to create the ExcelOntology from.
    :param project: The Project to use.
    :param working_dir: The working directory.
    :return: An ExcelOntology instance.
    """
    working_dir = working_dir if working_dir is not None else path.curdir

    ontology = ExcelOntology(project_file.target.iri)

    for source in project_file.sources:
        schema = project.spreadsheet_schema(source.spreadsheet_schema)
        if schema is None:
            ctx.log.error(
                type="schema-not-found",
                msg=f"Spreadsheet schema '{source.spreadsheet_schema}' not found.",
            )
            ctx.fail()

        if source.type == "classes":
            ctx.attempt(
                ontology.add_terms_from_excel(
                    source.file, path.join(working_dir, source.file), schema
                )
            )
        elif source.type == "relations":
            ctx.attempt(
                ontology.add_relations_from_excel(
                    source.file, path.join(working_dir, source.file), schema
                )
            )
        elif source.type == "individuals":
            ctx.log.error(
                type="not-implemented",
                msg=f"Source type '{source.type}' is not implemented yet.",
            )
        elif source.type == "owl":
            owl_ontology = ctx.attempt(
                ExcelOntology.from_owl(
                    path.join(working_dir, source.file), project.prefixes
                )
            )

            if owl_ontology is not None:
                ontology.merge_with(owl_ontology)

    if project_file.renameTermFile is not None:
        ontology.apply_renamings(project_file.renameTermFile)

    if project_file.addParentsFile is not None:
        ontology.apply_new_parents(project_file.addParentsFile)

    return ontology
