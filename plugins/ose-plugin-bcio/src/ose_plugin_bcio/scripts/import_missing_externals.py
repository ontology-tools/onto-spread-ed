import re
from datetime import datetime
from typing import Annotated, Dict

from github import Github
from injector import inject
import pyhornedowl

from ose_app.model.Script import Script
import ose_app.utils.github as github
from ose import constants
from ose.ontology.ExcelOntology import ExcelOntology, OntologyImport
from ose.schema.Term import Term
from ose.schema import termid
# from ose.routes.api.external import update_imports
from ose_app.services.ConfigurationService import ConfigurationService
from ose_app.utils.github import get_spreadsheets
from ose.utils import lower


class ImportMissingExternalsScript(Script):
    @property
    def id(self) -> str:
        return "import-missing-externals"

    @property
    def title(self) -> str:
        return "Import Missing Externals"

    @inject
    def __init__(self, gh: Github, config: ConfigurationService) -> None:
        super().__init__()
        self.gh = gh
        self.config = config

    def run(self, repo: Annotated[str, "Repository name"]) -> str:
        repository = self.config.get(repo)

        assert repository is not None, f"Repository configuration for '{repo}' not found."

        full_repo = repository.full_repository_name
        branch = repository.main_branch
        active_sheets = [source.file for file in repository.files.values() for source in file.sources
                         if source.type in ("classes", "relations")]
        regex = "|".join(f"({re.escape(r)})" for r in active_sheets) or r"(?!)"

        externals_owl = "addicto_external.owl"
        externals_content = github.get_file(self.gh, full_repo, externals_owl).decode()

        external_ontology = ExcelOntology(externals_owl)
        ontology = pyhornedowl.open_ontology(externals_content)
        for p, d in repository.prefixes.items():
            ontology.prefix_mapping.add_prefix(p, d)

        for c in ontology.get_classes():
            id = ontology.get_id_for_iri(c)
            labels = ontology.get_annotations(c, constants.RDFS_LABEL)

            if id is not None:
                for label in labels:
                    external_ontology.add_term(
                        Term(
                            id=id,
                            label=label,
                            origin=("<external>", -1),
                            relations=[],
                            sub_class_of=[],
                            equivalent_to=[],
                            disjoint_with=[],
                        )
                    )

        excel_files = get_spreadsheets(self.gh, full_repo, branch, include_pattern=regex)

        missing_imports: Dict[str, OntologyImport] = {}

        for file in excel_files:
            content = github.get_file(self.gh, full_repo, file)
            o = ExcelOntology(file)
            o.add_terms_from_excel(file, content)

            for t in o._terms:
                if (
                    t.id is not None
                    and lower(t.curation_status()) == "external"
                    and external_ontology.term_by_id(t.id) is None
                ):
                    pref = t.id.split(":")[0]
                    imp = missing_imports.setdefault(
                        pref,
                        OntologyImport(
                            id=pref,
                            iri=f"http://purl.obolibrary.org/obo/{pref.lower()}.owl",
                            root_id=termid(id="BFO:0000001", label="entity"),
                            intermediates="all",
                            prefixes=[],
                            imported_terms=[],
                        ),
                    )

                    imp.imported_terms.append(t.identifier())

        change_branch = f"script/import-missing-{datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')}"
        github.create_branch(self.gh, full_repo, change_branch, branch)


        # update_imports(repo, full_repo, self.gh, list(missing_imports.values()), change_branch)

        body = "Imported the terms:\n"
        body += "\n\n".join(
            f"{m.id}: \n" + "\n".join(f"  - {t.label} [{t.id}]" for t in m.imported_terms)
            for m in missing_imports.values()
        )

        pr = github.create_pr(self.gh, full_repo, "Import missing external terms", body, change_branch, branch)
        github.merge_pr(self.gh, full_repo, pr)

        return "<p>Imported the terms:</p>\n" + "\n".join(
            f"<p>{m.id}: \n<ul>" + "\n".join(f"<li>{t.label} [{t.id}]</li>" for t in m.imported_terms) + "</ul></p>"
            for m in missing_imports.values()
        )
