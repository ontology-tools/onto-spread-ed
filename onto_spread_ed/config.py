import logging
import os

APP_TITLE = "Ontology Spreadsheet Editor"
ENVIRONMENT = os.environ.get("FLASK_ENV")
URL_PREFIX = '/onto-ed'

ENVIRONMENT = os.environ.get("FLASK_ENV")

DATABASE_URI = os.environ.get("DATABASE_URI", 'sqlite:////tmp/github-flask-ontospreaded.db')
SQLALCHEMY_DATABASE_URI = DATABASE_URI

RELEASE_FILES = {"AddictO": "addicto.owl",
                 "BCIO": "Upper%20Level%20BCIO/bcio.owl",
                 "GMHO": "gmho.owl"}

PREFIXES = [["ADDICTO", "http://addictovocab.org/ADDICTO_"],
            ["BFO", "http://purl.obolibrary.org/obo/BFO_"],
            ["COB", "http://purl.obolibrary.org/obo/COB_"],
            ["CHEBI", "http://purl.obolibrary.org/obo/CHEBI_"],
            ["UBERON", "http://purl.obolibrary.org/obo/UBERON_"],
            ["PATO", "http://purl.obolibrary.org/obo/PATO_"],
            ["BCIO", "http://humanbehaviourchange.org/ontology/BCIO_"],
            ["GMHO", "https://galenos.org.uk/ontology/GMHO_"],
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
            ["GO", "http://purl.obolibrary.org/obo/GO_"]
            ]
# Spreadsheets that should be included in the index and by default selected to be included in the release
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
        r".*\.xlsx"
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

RDFSLABEL = "http://www.w3.org/2000/01/rdf-schema#label"

DIGIT_COUNT = 7

LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", "WARNING").upper())
if not isinstance(LOG_LEVEL, int):
    raise ValueError('Invalid log level: %s' % LOG_LEVEL)
logging.basicConfig(level=LOG_LEVEL)

DEPLOYMENT_MODE = os.environ.get("INDEX_STORAGE", "LOCAL").upper()
"""
How the app is deployed and gets is configuration. Possible values are "GOOGLE_CLOUD", "LOCAL"
"""
if DEPLOYMENT_MODE not in ["GOOGLE_CLOUD", "LOCAL"]:
    DEPLOYMENT_MODE = "LOCAL"

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')

if os.environ.get("FLASK_ENV") == 'development':
    REPOSITORIES = {
        "BCIO": "b-gehrke/ontologies",
        "AddictO": "b-gehrke/addiction-ontology",
        "GMHO": "b-gehrke/mental-health-ontology",
        "BCIO": "zaidishz/ontologies",
        "BCIO": "nitinbharadwajnataraj/ontologies"
    }
else:
    REPOSITORIES = {
        "AddictO": "addicto-org/addiction-ontology",
        "BCIO": "HumanBehaviourChangeProject/ontologies",
        "GMHO": "galenos-project/mental-health-ontology",
        "BCIO": "zaidishz/ontologies",
        "BCIO": "nitinbharadwajnataraj/ontologies"
    }

DEFAULT_BRANCH = {
    "BCIO": "master",
    "AddictO": "master",
    "GMHO": "main"
}

if DEPLOYMENT_MODE == "GOOGLE_CLOUD":
    # Connect to the Google cloud Secret Manager client
    from google.cloud import secretmanager
    # Connect to Google cloud storage client
    from google.cloud import storage

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS",
                                                                  'ontospreaded.json')
    # Cloud storage - for the index search
    storage_client = storage.Client()
    GOOGLE_INDEX_BUCKET = os.environ.get("GOOGLE_INDEX_BUCKET", 'index-spread-ed')
    bucket = storage_client.get_bucket(GOOGLE_INDEX_BUCKET)

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID", "")
    GOOGLE_SECRET_NAME_GITHUB_CLIENT_ID = os.environ.get("GOOGLE_SECRET_NAME_GITHUB_CLIENT_ID", "GITHUB_CLIENT_ID")
    # Build the resource name of the secret version.
    name = f"projects/{GOOGLE_PROJECT_ID}/secrets/{GOOGLE_SECRET_NAME_GITHUB_CLIENT_ID}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    GITHUB_CLIENT_ID = response.payload.data.decode("UTF-8")

    GOOGLE_SECRET_NAME_GITHUB_CLIENT_SECRET = os.environ.get("GOOGLE_SECRET_NAME_GITHUB_CLIENT_SECRET",
                                                             "GITHUB_CLIENT_SECRET")
    # Build the resource name of the secret version.
    name = f"projects/{GOOGLE_PROJECT_ID}/secrets/{GOOGLE_SECRET_NAME_GITHUB_CLIENT_SECRET}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    GITHUB_CLIENT_SECRET = response.payload.data.decode("UTF-8")

    GOOGLE_SECRET_NAME_FLASK_SECRET = os.environ.get("GOOGLE_SECRET_NAME_FLASK_SECRET", "FLASK_SECRET_KEY")
    # Build the resource name of the secret version.
    name = f"projects/{GOOGLE_PROJECT_ID}/secrets/{GOOGLE_SECRET_NAME_FLASK_SECRET}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    SECRET_KEY = response.payload.data.decode("UTF-8")
elif DEPLOYMENT_MODE == "LOCAL":
    INDEX_PATH = os.environ.get("INDEX_PATH")

USERS_METADATA = {"tomjuggler": {"initials": "ZZ", "repositories": ["AddictO", "BCIO"]},
                  "jannahastings": {"initials": "JH", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "robertjwest": {"initials": "RW", "repositories": ["AddictO", "BCIO", "GMHO"]},
                  "sharoncox": {"initials": "SC", "repositories": ["AddictO"]},
                  "ksoar": {"initials": "KS", "repositories": ["AddictO"]},
                  "CaitlinNotley702": {"initials": "CN", "repositories": ["AddictO"]},
                  "CaitlinNotley": {"initials": "CN", "repositories": ["AddictO"]},
                  "alisonjwright": {"initials": "AW", "repositories": ["BCIO", "AddictO"]},
                  "zcbtelh": {"initials": "EH", "repositories": ["BCIO"]},
                  "candicemooreucl": {"initials": "CM", "repositories": ["BCIO"]},
                  "oscarcastroserrano": {"initials": "OC", "repositories": ["BCIO"]},
                  "emilyjhayes": {"initials": "EJH", "repositories": ["BCIO"]},
                  "paulinaschenk": {"initials": "PS", "repositories": ["BCIO", "GMHO"], "admin": True},
                  "lzhang01": {"initials": "LZ", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "b-gehrke": {"initials": "BG", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "zaidishz": {"initials": "HZ", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "nitinbharadwajnataraj": {"initials": "NB", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True}
                  }
ALL_USERS_INITIALS = [v["initials"] for v in USERS_METADATA.values()]

BCIO_SEARCH_API_PATH = "https://api.bciosearch.org/"
