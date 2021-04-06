import os

# Connect to the Google cloud Secret Manager client
from google.cloud import secretmanager
# Connect to Google cloud storage client
from google.cloud import storage

DEBUG = True

APP_TITLE = "Ontology Spreadsheet Editor"

DATABASE_URI = 'sqlite:////tmp/github-flask-ontospreaded.db'

RELEASE_FILES = {"AddictO": "addicto-merged.owx",
                 "BCIO": "Upper%20Level%20BCIO/bcio-merged.owx"}

PREFIXES = [ ["ADDICTO","http://addictovocab.org/ADDICTO_"],
             ["BFO","http://purl.obolibrary.org/obo/BFO_"],
             ["CHEBI","http://purl.obolibrary.org/obo/CHEBI_"],
             ["UBERON","http://purl.obolibrary.org/obo/UBERON_"],
             ["PATO","http://purl.obolibrary.org/obo/PATO_"],
             ["BCIO","http://humanbehaviourchange.org/ontology/BCIO_"],
             ["SEPIO","http://purl.obolibrary.org/obo/SEPIO_"],
             ["OMRSE","http://purl.obolibrary.org/obo/OMRSE_"],
             ["OBCS","http://purl.obolibrary.org/obo/OBCS_"],
             ["OGMS","http://purl.obolibrary.org/obo/OGMS_"],
             ["ENVO","http://purl.obolibrary.org/obo/ENVO_"],
             ["OBI", "http://purl.obolibrary.org/obo/OBI_"],
             ["MFOEM","http://purl.obolibrary.org/obo/MFOEM_"],
             ["MF","http://purl.obolibrary.org/obo/MF_"],
             ["CHMO","http://purl.obolibrary.org/obo/CHMO_"],
             ["DOID","http://purl.obolibrary.org/obo/DOID_"],
             ["IAO","http://purl.obolibrary.org/obo/IAO_"],
             ["ERO","http://purl.obolibrary.org/obo/ERO_"],
             ["PO","http://purl.obolibrary.org/obo/PO_"],
             ["RO","http://purl.obolibrary.org/obo/RO_"],
             ["APOLLO_SV","http://purl.obolibrary.org/obo/APOLLO_SV_"],
             ["PDRO","http://purl.obolibrary.org/obo/PDRO_"],
             ["GAZ","http://purl.obolibrary.org/obo/GAZ_"]
           ]

RDFSLABEL = "http://www.w3.org/2000/01/rdf-schema#label"

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
