import os

# Connect to the Google cloud Secret Manager client
from google.cloud import secretmanager
# Connect to Google cloud storage client
from google.cloud import storage


DEBUG = True

APP_TITLE = "Ontology Spreadsheet Editor"

DATABASE_URI = 'sqlite:////tmp/github-flask-ontospreaded.db'

RELEASE_FILES = {"AddictO": "addicto.owx", "BCIO": "bcio.owx"}

if os.environ.get("FLASK_ENV")=='development':
    GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    REPOSITORIES = {"AddictO": "jannahastings/addiction-ontology", "BCIO": "jannahastings/ontologies"}
    # onto-spread-ed google credentials in local directory for dev mode
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']='ontospreaded.json'
    # Cloud storage - for the index search
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('index-spread-ed-dev')

else:
    REPOSITORIES = {"AddictO": "addicto-org/addiction-ontology", "BCIO": "HumanBehaviourChangeProject/ontologies"}
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'ontospreaded.json'
    # Cloud storage - for the index search
    storage_client = storage.Client()
    bucket = storage_client.get_bucket('index-spread-ed')

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    project_id = "onto-spread-ed"
    client_id = "GITHUB_CLIENT_ID"
    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{client_id}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    GITHUB_CLIENT_ID = response.payload.data.decode("UTF-8")

    client_secret = "GITHUB_CLIENT_SECRET"
    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{client_secret}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    GITHUB_CLIENT_SECRET = response.payload.data.decode("UTF-8")

    flask_secret = "FLASK_SECRET_KEY"
    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{flask_secret}/versions/latest"
    # Access the secret version.
    response = client.access_secret_version(request={"name": name})
    SECRET_KEY = response.payload.data.decode("UTF-8")

USERS_METADATA = {"jannahastings": {"initials":"JH", "repositories":["AddictO","BCIO"]},
                  "robertjwest": {"initials":"RW", "repositories":["AddictO","BCIO"]},
                  "sharoncox":{"initials":"SC", "repositories":["AddictO"]},
                  "ksoar":{"initials":"KS", "repositories":["AddictO"]},
                  "CaitlinNotley702": {"initials":"CN", "repositories":["AddictO"]},
                  "CaitlinNotley": {"initials":"CN", "repositories":["AddictO"]},
                  "alisonjwright":{"initials":"AW", "repositories":["BCIO","AddictO"]},
                  "zcbtelh": {"initials":"EH", "repositories":["BCIO"]},
                  "candicemooreucl": {"initials":"CM", "repositories":["BCIO"]},
                  "oscarcastroserrano": {"initials":"OC", "repositories":["BCIO"]},
                  "emilyjhayes": {"initials":"EJH", "repositories":["BCIO"]}}
ALL_USERS_INITIALS = [v["initials"] for v in USERS_METADATA.values()]
