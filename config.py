import logging
import os

APP_TITLE = "Ontology Spreadsheet Editor"

DATABASE_URI = 'sqlite:////tmp/github-flask-ontospreaded.db'

RELEASE_FILES = {"AddictO": "addicto-merged.owx",
                 "BCIO": "Upper%20Level%20BCIO/bcio.owl"}

PREFIXES = [["ADDICTO", "http://addictovocab.org/ADDICTO_"],
            ["BFO", "http://purl.obolibrary.org/obo/BFO_"],
            ["CHEBI", "http://purl.obolibrary.org/obo/CHEBI_"],
            ["UBERON", "http://purl.obolibrary.org/obo/UBERON_"],
            ["PATO", "http://purl.obolibrary.org/obo/PATO_"],
            ["BCIO", "http://humanbehaviourchange.org/ontology/BCIO_"],
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
# Spreadsheets that should be included in the index and are later used in a release
ACTIVE_SPREADSHEETS = {
    "BCIO": [
        "Setting/inputs/Setting.xlsx",
        "ModeOfDelivery/inputs/MoD.xlsx",
        "Source/inputs/BCIO_Source.xlsx",
        "MechanismOfAction/inputs/BCIO_MoA.xlsx",
        "Behaviour/BCIO_behaviour.xlsx",
        "BehaviourChangeTechniques/inputs/BCIO_BehaviourChangeTechniques.xlsx",
        "StyleOfDelivery/BCIO_StyleOfDelivery.xlsx",
        r"Upper Level BCIO/inputs/.*\.xlsx"
    ],
    "AddictO": [
        r".*\.xlsx"
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
    REPOSITORIES = {"BCIO": "b-gehrke/ontologies", "AddictO": "b-gehrke/addiction-ontology"}
else:
    REPOSITORIES = {"AddictO": "addicto-org/addiction-ontology", "BCIO": "HumanBehaviourChangeProject/ontologies"}

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

    GOOGLE_PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID", "onto-spread-ed")
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
                  "jannahastings": {"initials": "JH", "repositories": ["AddictO", "BCIO"], "admin": True},
                  "robertjwest": {"initials": "RW", "repositories": ["AddictO", "BCIO"]},
                  "sharoncox": {"initials": "SC", "repositories": ["AddictO"]},
                  "ksoar": {"initials": "KS", "repositories": ["AddictO"]},
                  "CaitlinNotley702": {"initials": "CN", "repositories": ["AddictO"]},
                  "CaitlinNotley": {"initials": "CN", "repositories": ["AddictO"]},
                  "alisonjwright": {"initials": "AW", "repositories": ["BCIO", "AddictO"]},
                  "zcbtelh": {"initials": "EH", "repositories": ["BCIO"]},
                  "candicemooreucl": {"initials": "CM", "repositories": ["BCIO"]},
                  "oscarcastroserrano": {"initials": "OC", "repositories": ["BCIO"]},
                  "emilyjhayes": {"initials": "EJH", "repositories": ["BCIO"]},
                  "paulinaschenk": {"initials": "PS", "repositories": ["BCIO"]},
                  "b-gehrke": {"initials": "BG", "repositories": ["AddictO", "BCIO"], "admin": True}}
ALL_USERS_INITIALS = [v["initials"] for v in USERS_METADATA.values()]
