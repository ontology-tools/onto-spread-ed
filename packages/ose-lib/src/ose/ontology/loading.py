from os import path

from ose.project import ProjectFile, Project
from ose.result import Result, Log, is_successful
from ose.ontology.ExcelOntology import ExcelOntology


def from_project_file(
    project_file: ProjectFile,
    project: Project,
    working_dir: str | None = None,
) -> Result[ExcelOntology]:
    """
    Create an ExcelOntology from a ProjectFile.

    :param project_file: The ProjectFile to create the ExcelOntology from.
    :param project: The Project to use.
    :param working_dir: The working directory.
    :return: An ExcelOntology instance.
    """
    log = Log()

    working_dir = working_dir if working_dir is not None else path.curdir

    ontology = ExcelOntology(project_file.target.iri)

    for source in project_file.sources:
        schema = project.spreadsheet_schema(source.spreadsheet_schema)
        if schema is None:
            log.error(
                type="schema-not-found",
                msg=f"Spreadsheet schema '{source.spreadsheet_schema}' not found.",
            )
            return log.fail()

        if source.type == "classes":
            ontology.add_terms_from_excel(
                source.file, path.join(working_dir, source.file), schema
            )
        elif source.type == "relations":
            ontology.add_relations_from_excel(
                source.file, path.join(working_dir, source.file), schema
            )
        elif source.type == "individuals":
            log.error(
                type="not-implemented",
                msg=f"Source type '{source.type}' is not implemented yet.",
            )
        elif source.type == "owl":
            owl_ontology_result = ExcelOntology.from_owl(
                path.join(working_dir, source.file), project.prefixes
            )

            log += owl_ontology_result.log

            if is_successful(owl_ontology_result):
                ontology.merge_with(owl_ontology_result.value)

    if project_file.renameTermFile is not None:
        ontology.apply_renamings(project_file.renameTermFile)

    if project_file.addParentsFile is not None:
        ontology.apply_new_parents(project_file.addParentsFile)

    return log.to_result(ontology)
