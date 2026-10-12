from collections.abc import Sequence
import pickle
import logging
import re
import traceback
from flask import Blueprint, g, jsonify

from ose_app.guards.with_permission import requires_permissions
from ose.ontology import ExcelOntology
from ose.project import ProjectFile
from ose.schema import Term, UnresolvedTerm, TermIdentifier
from ose_app.services.FileCache import FileCache
from ose_app.services.ConfigurationService import ConfigurationService

logger = logging.getLogger(__name__)

bp = Blueprint("api_visualise", __name__, url_prefix="/api/visualise")


@bp.route("/dependencies/<string:repo>/<path:path>", methods=["GET"])
@requires_permissions("view")
def get_dependencies(
    repo: str, path: str, config: ConfigurationService, cache: FileCache
):
    """
    Get dependencies and derived spreadsheet data for a given spreadsheet.
    Returns term data that can be combined with the current spreadsheet data on the frontend.
    Results are cached based on repo, path, and file SHA.
    """
    user_name = g.user.github_login if g.user else "*"
    user_repos = (
        config.app_config["USERS"]
        .get(user_name, config.app_config["USERS"].get("*", {}))
        .get("repositories", [])
    )

    if repo not in user_repos:
        return jsonify({"msg": f"No such repository '{repo}'", "success": False}), 404

    try:
        logger.info(f"Loading dependencies for {repo}/{path}")

        # Get file SHA for cache key
        project = config.get(repo)
        if project is None:
            logger.error(f"Repository configuration not found for: {repo}")
            return (
                jsonify(
                    {"msg": "Repository configuration not found", "success": False}
                ),
                500,
            )

        # Try to get from cache first
        cache_key = re.sub(r'[^a-zA-Z0-9-_]', '_', f"visualisation_deps_{repo}_{path}")
        cached_data = cache.retrieve(cache_key)
        if cached_data:
            logger.debug(f"Returning cached data for {cache_key}")
            ontology_data = pickle.loads(cached_data)
            return jsonify({"success": True, "data": ontology_data}), 200

        logger.debug(f"Cache miss for {cache_key}, loading from source")

        # Load externals
        logger.debug(f"Loading externals from {project.external.target.file}")
        externals_owl = config.get_file(project, project.external.target.file)
        if externals_owl is None:
            raise ValueError(f"External file '{project.external.target.file}' not found")
        externals_ontology = ExcelOntology.from_owl(
            externals_owl,
            project.prefixes,
            "dependency:" + project.external.target.file,
        ).value_or_raise()
        logger.debug(f"Externals loaded: {len(list(externals_ontology.terms()))} terms")

        # Load derived
        def get_derived(file: ProjectFile) -> list[ProjectFile]:
            name = next(n for n, f in project.files.items() if f == file)
            derived: list[ProjectFile] = [
                s for s in project.files.values() if name in s.needs
            ]
            return derived + [item for s in derived for item in get_derived(s)]

        logger.debug(f"Finding project file for path: {path}")
        try:
            project_file = next(
                f
                for f in project.files.values()
                if path in [s.file for s in f.sources]
            )
        except StopIteration:
            logger.error(f"No project file found for path: {path}")
            logger.debug(
                f"Available paths: {[s.file for f in project.files.values() for s in f.sources]}"
            )
            return (
                jsonify(
                    {
                        "msg": f"Path not found in project: {path}",
                        "success": False,
                    }
                ),
                404,
            )

        logger.debug("Loading derived files")
        derived = get_derived(project_file)
        derived = [
            d for i, d in enumerate(derived) if d not in derived[:i]
        ]  # Remove duplicates
        logger.debug(f"Found {len(derived)} derived files")

        terms_iri = f"file:///tmp/{repo}/{path}"
        derived_ontology = ExcelOntology(terms_iri + "/derived")
        for der in derived:
            for source in der.sources:
                if source.type == "classes":
                    xlsx = config.get_file_raw(project, source.file)
                    if xlsx is None:
                        raise ValueError(f"File '{source.file}' not found")
                    derived_ontology.add_terms_from_excel(
                        source.file, xlsx, project.spreadsheet_schema(source.spreadsheet_schema)
                    )
                elif source.type == "owl":
                    owl_data = config.get_file(project, source.file)
                    if owl_data is None:
                        raise ValueError(f"File '{source.file}' not found")
                    owl_ontology = ExcelOntology.from_owl(
                        owl_data, project.prefixes
                    ).value_or_raise()
                    derived_ontology.merge_with(owl_ontology)

        # Load dependencies
        def get_dependencies_recursive(
            file: ProjectFile,
        ) -> list[ProjectFile]:
            dependencies: list[ProjectFile] = [
                s for n, s in project.files.items() if n in file.needs
            ]
            return dependencies + [
                item for s in dependencies for item in get_dependencies_recursive(s)
            ]

        logger.debug("Loading dependency files")
        dependencies = get_dependencies_recursive(project_file)
        dependencies = [
            d for i, d in enumerate(dependencies) if d not in dependencies[:i]
        ]  # Remove duplicates
        logger.debug(f"Found {len(dependencies)} dependency files")

        dependencies_ontology = ExcelOntology(terms_iri + "/dependencies")
        dependencies_ontology.merge_with(externals_ontology)
        for dep in dependencies:
            for source in dep.sources:
                if source.type == "classes":
                    xlsx = config.get_file_raw(project, source.file)
                    if xlsx is None:
                        raise ValueError(f"File '{source.file}' not found")
                    dependencies_ontology.add_terms_from_excel(
                        "dependency:" + source.file, xlsx, project.spreadsheet_schema(source.spreadsheet_schema)
                    )
                elif source.type == "owl":
                    owl_data = config.get_file(project, source.file)
                    if owl_data is None:
                        raise ValueError(f"File '{source.file}' not found")
                    owl_ontology = ExcelOntology.from_owl(
                        owl_data,
                        project.prefixes,
                        origin="dependency:" + source.file,
                    ).value_or_raise()
                    dependencies_ontology.merge_with(owl_ontology)

        derived_ontology.import_other_excel_ontology(dependencies_ontology)
        derived_ontology.resolve()

        # Serialize ontology terms to JSON format
        def terms_to_json(terms_list: Sequence[Term | UnresolvedTerm]) -> list[dict]:
            result = []
            for term in terms_list:
                term_data = {
                    "id": term.id,
                    "label": term.label,
                    "curationStatus": term.curation_status() or "External",
                    "origin": term.origin[0] if term.origin else "<unknown>",
                    "subClassOf": [
                        {"id": p.id, "label": p.label}
                        for p in term.sub_class_of
                        if p.id is not None
                    ],
                    "relations": [
                        {
                            "relation": {"label": rel.label},
                            "target": {"id": target.id, "label": target.label},
                        }
                        for rel, target in term.relations
                        if isinstance(target, (Term, TermIdentifier)) and rel.label
                    ],
                }
                result.append(term_data)
            return result

        dependency_terms = [t for t in dependencies_ontology.terms()]
        derived_terms = [t for t in derived_ontology._terms]

        logger.info(
            f"Successfully loaded {len(dependency_terms)} dependency terms and {len(derived_terms)} derived terms"
        )

        ontology_data = {
            "dependencies": terms_to_json(dependency_terms),
            "derived": terms_to_json(derived_terms),
        }

        # Cache the result
        cache.store(cache_key, pickle.dumps(ontology_data))
        logger.debug(f"Cached result for {cache_key}")

        return jsonify({"success": True, "data": ontology_data}), 200

    except Exception as e:
        logger.error(f"Error loading dependencies for {repo}/{path}: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            jsonify({"success": False, "error": f"{type(e).__name__}: {str(e)}"}),
            500,
        )
