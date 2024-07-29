import logging
import os

APP_TITLE = "Ontology Spreadsheet Editor"
ENVIRONMENT = os.environ.get("FLASK_ENV")
URL_PREFIX = ''

DATABASE_URI = os.environ.get("DATABASE_URI", 'sqlite:////tmp/github-flask-ontospreaded.db')
SQLALCHEMY_DATABASE_URI = DATABASE_URI


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
                  "robertjwest": {"initials": "RW", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "sharoncox": {"initials": "SC", "repositories": ["AddictO"]},
                  "ksoar": {"initials": "KS", "repositories": ["AddictO"]},
                  "CaitlinNotley702": {"initials": "CN", "repositories": ["AddictO"]},
                  "CaitlinNotley": {"initials": "CN", "repositories": ["AddictO"]},
                  "alisonjwright": {"initials": "AW", "repositories": ["BCIO", "AddictO"], "admin": True},
                  "zcbtelh": {"initials": "EH", "repositories": ["BCIO"]},
                  "candicemooreucl": {"initials": "CM", "repositories": ["BCIO"]},
                  "oscarcastroserrano": {"initials": "OC", "repositories": ["BCIO"]},
                  "emilyjhayes": {"initials": "EJH", "repositories": ["BCIO"]},
                  "paulinaschenk": {"initials": "PS", "repositories": ["BCIO", "GMHO"], "admin": True},
                  "lzhang01": {"initials": "LZ", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "b-gehrke": {"initials": "BG", "repositories": ["AddictO", "BCIO", "GMHO"], "admin": True},
                  "micaelasantilli": {"initials": "MS", "repositories": ["BCIO", "GMHO"], "admin": True},
                  }
ALL_USERS_INITIALS = [v["initials"] for v in USERS_METADATA.values()]

BCIO_SEARCH_API_PATH = "https://api.bciosearch.org/"

SCRIPTS = {
    "set-pre-proposed-curation-status": {
        "title": "Set 'Pre-proposed' state",
        "module": "scripts.set-pre-proposed-curation-status",
        "function": "main",
        "arguments": [
            {
                "name": "repo",
                "description": "Which repository should the script be executed?",
                "type": "string",
                "default": "AddictO"
            }
        ]
    },
    "import-missing-externals": {
        "title": "Import missing 'External' terms",
        "module": "scripts.import-missing-externals",
        "function": "main",
        "arguments": [
            {
                "name": "repo",
                "description": "Which repository should the script be executed?",
                "type": "string"
            }
        ]
    }
}
