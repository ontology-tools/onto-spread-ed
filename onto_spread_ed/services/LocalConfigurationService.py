import os
from typing import Dict, Optional, List

from flask import current_app

from onto_spread_ed.model.RepositoryConfiguration import RepositoryConfiguration, SubOntologyConfiguration
from onto_spread_ed.services.ConfigurationService import ConfigurationService

RELEASE_FILES = {
    "AddictO": "addicto.owl",
    "BCIO": "Upper%20Level%20BCIO/bcio.owl",
    "GMHO": "gmho.owl",
}

if os.environ.get("FLASK_ENV") == 'development':
    REPOSITORIES = {
        "BCIO": "b-gehrke/ontologies",
        "AddictO": "b-gehrke/addiction-ontology",
        "GMHO": "b-gehrke/mental-health-ontology"
    }
else:
    REPOSITORIES = {
        "AddictO": "addicto-org/addiction-ontology",
        "BCIO": "HumanBehaviourChangeProject/ontologies",
        "GMHO": "galenos-project/mental-health-ontology"
    }

DEFAULT_BRANCH = {
    "BCIO": "master",
    "AddictO": "master",
    "GMHO": "main"
}

SUB_ONTOLOGIES = {
    "BCIO": {
        "setting": {
            "release_file": "Setting/bcio_setting.owl",
            "excel_file": "Setting/bcio_setting.xlsx"
        },
        "mode_of_delivery": {
            "release_file": "ModeOfDelivery/bcio_mode_of_delivery.owl",
            "excel_file": "ModeOfDelivery/bcio_mode_of_delivery.xlsx"
        },
        "source": {
            "release_file": "Source/bcio_source.owl",
            "excel_file": "Source/bcio_source.xlsx"
        },
        "moa": {
            "release_file": "MechanismOfAction/bcio_moa.owl",
            "excel_file": "MechanismOfAction/bcio_moa.xlsx"
        },
        "behaviour": {
            "release_file": "Behaviour/bcio_behaviour.owl",
            "excel_file": "Behaviour/bcio_behaviour.xlsx"
        },
        "bcto": {
            "release_file": "BehaviourChangeTechniques/bcto.owl",
            "excel_file": "BehaviourChangeTechniques/bcto.xlsx"
        },
        "style": {
            "release_file": "StyleOfDelivery/bcio_style.owl",
            "excel_file": "StyleOfDelivery/bcio_style.xlsx"
        },
    }
}

PREFIXES = [["ADDICTO", "http://addictovocab.org/ADDICTO_"],
            ["BFO", "http://purl.obolibrary.org/obo/BFO_"],
            ["COB", "http://purl.obolibrary.org/obo/COB_"],
            ["CHEBI", "http://purl.obolibrary.org/obo/CHEBI_"],
            ["UBERON", "http://purl.obolibrary.org/obo/UBERON_"],
            ["PATO", "http://purl.obolibrary.org/obo/PATO_"],
            ["BCIO", "http://humanbehaviourchange.org/ontology/BCIO_"],
            ["GMHO", "https://galenos.org.uk/ontologies/GMHO_"],
            ["SEPIO", "http://purl.obolibrary.org/obo/SEPIO_"],
            ["OMRSE", "http://purl.obolibrary.org/obo/OMRSE_"],
            ["OBCS", "http://purl.obolibrary.org/obo/OBCS_"],
            ["OGMS", "http://purl.obolibrary.org/obo/OGMS_"],
            ["ENVO", "http://purl.obolibrary.org/obo/ENVO_"],
            ["OBI", "http://purl.obolibrary.org/obo/OBI_"],
            ["MFOEM", "http://purl.obolibrary.org/obo/MFOEM_"],
            ["MF", "http://purl.obolibrary.org/obo/MF_"],
            ["CHMO", "http://purl.obolibrary.org/obo/CHMO_"],
            ["DOID", "http://purl.obolibrary.org/obo/DOID_"],
            ["IAO", "http://purl.obolibrary.org/obo/IAO_"],
            ["ERO", "http://purl.obolibrary.org/obo/ERO_"],
            ["PO", "http://purl.obolibrary.org/obo/PO_"],
            ["RO", "http://purl.obolibrary.org/obo/RO_"],
            ["APOLLO_SV", "http://purl.obolibrary.org/obo/APOLLO_SV_"],
            ["PDRO", "http://purl.obolibrary.org/obo/PDRO_"],
            ["GAZ", "http://purl.obolibrary.org/obo/GAZ_"],
            ["GSSO", "http://purl.obolibrary.org/obo/GSSO_"],
            ["GO", "http://purl.obolibrary.org/obo/GO_"],
            ["EFO", "http://www.ebi.ac.uk/efo/EFO_"],
            ["PR", "http://purl.obolibrary.org/obo/PR_"],
            ["STATO", "http://purl.obolibrary.org/obo/STATO_"],
            ["OMIABIS", "http://purl.obolibrary.org/obo/OMIABIS_"],
            ["OPMI", "http://purl.obolibrary.org/obo/OPMI_"],
            ["CMO", "http://purl.obolibrary.org/obo/CMO_"],
            ["OBCS", "http://purl.obolibrary.org/obo/OBCS_"],
            ["OAE", "http://purl.obolibrary.org/obo/OAE_"],
            ["NCIT", "http://purl.obolibrary.org/obo/NCIT_"],
            ["HP", "http://purl.obolibrary.org/obo/HP_"],
            ["SDGIO", "http://purl.unep.org/sdg/SDGIO_"],
            ["SIO", "http://semanticscience.org/resource/SIO_"]
            ]

ACTIVE_SPREADSHEETS = {
    "BCIO": [
        "Setting/bcio_setting.xlsx",
        "ModeOfDelivery/bcio_mode_of_delivery.xlsx",
        "Source/bcio_source.xlsx",
        "MechanismOfAction/bcio_moa.xlsx",
        "Behaviour/bcio_behaviour.xlsx",
        "BehaviourChangeTechniques/bcto.xlsx",
        "StyleOfDelivery/bcio_style.xlsx",
        r"Upper Level BCIO/inputs/.*\.xlsx"
    ],
    "AddictO": [
        r"inputs/.*\.xlsx"
    ],
    "GMHO": [
        "Non-GMHO entities mapped to LSRs/Non-GMHO entities mapped to LSRs.xlsx",
        "Intervention mechanism/Intervention mechanism of action.xlsx",
        "Intervention setting/Intervention setting.xlsx",
        "Intervention population/Intervention population.xlsx",
        "Intervention outcomes and spillover effects/Intervention outcomes and spillover effects.xlsx",
        "Intervention content and delivery/Intervention content and delivery.xlsx",
        "Research methods/Research methods.xlsx",
    ]
}

REPOS = dict((k,
              RepositoryConfiguration(
                  short_name=k,
                  full_name=full,
                  main_branch=DEFAULT_BRANCH[k],
                  prefixes=dict(PREFIXES),
                  release_file=RELEASE_FILES[k],
                  indexed_files=ACTIVE_SPREADSHEETS[k],
              release_script_path=f"{k.lower()}.release.json",  
                  id_digits=7,
                  subontologies=dict(
                      (k, SubOntologyConfiguration(
                          release_file=s['release_file'],
                          excel_file=s['excel_file']
                      )) for k, s in SUB_ONTOLOGIES.get(k, {}).items()
                  )
              )) for k, full in REPOSITORIES.items())


class LocalConfigurationService(ConfigurationService):

    def __init__(self, app_config, *args, **kwargs):
        super().__init__(app_config)

    def get_by_short_name(self, short_name: str) -> Optional[RepositoryConfiguration]:
        return REPOS.get(short_name, None)

    def get_by_full_name(self, full_name: str) -> Optional[RepositoryConfiguration]:
        short = next((s for s, f in REPOS.items() if f.full_name == full_name), None)
        return self.get_by_short_name(short)

    def get_by_url(self, url: str) -> Optional[RepositoryConfiguration]:
        short = next((s for s, f in REPOS.items() if url.endswith(f.full_name)), None)
        return self.get_by_short_name(short)

    def loaded_repositories(self) -> List[RepositoryConfiguration]:
        return list(REPOS.values())

    def get_file(self, config: RepositoryConfiguration, path: str) -> Optional[str]:
        path = os.path.join(current_app.static_folder, path)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read()

        return None

    def unload(self, name: str) -> bool:
        key = next((k for k,v in REPOS.items() if v.full_name == name or v.short_name == name), None)
        if key is not None:
            del REPOS[key]
            return True

        return False





