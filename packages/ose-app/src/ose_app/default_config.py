import logging
import os

APP_TITLE = "Ontology Spreadsheet Editor"
ENVIRONMENT = os.environ.get("FLASK_ENV")
URL_PREFIX = ''

DATABASE_URI = 'sqlite:////tmp/github-flask-ontospreaded.db'
INDEX_PATH = "ose_index"

LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", "WARNING").upper())
if not isinstance(LOG_LEVEL, int):
    raise ValueError('Invalid log level: %s' % LOG_LEVEL)
logging.basicConfig(level=LOG_LEVEL)

GITHUB_CLIENT_ID = None
GITHUB_CLIENT_SECRET = None

CACHE_DIR = os.path.join(os.environ.get("HOME", "/"), ".cache", "ose")
CACHE_LIFE_TIME = None

USERS = dict()

CONFIGURATION = "repository"
REPOSITORIES_REPOSITORY_CONFIG_DEFAULT_REPOSITORIES = []
REPOSITORIES_REPOSITORY_CONFIG_ALLOW_LOAD = False
REPOSITORIES_REPOSITORY_CONFIG_ALLOW_SAVE = False
REPOSITORIES_REPOSITORY_CONFIG_PATH = '.onto-ed/config.yaml'
REPOSITORIES_REPOSITORY_CONFIG_STARTUP_REPOSITORIES_PATH = 'startup-repositories.yaml'
REPOSITORIES_REPOSITORY_CONFIG_BASE_URL = 'repos/{full_name}/contents/{path}'
REPOSITORIES_REPOSITORY_CONFIG_REQUEST_HEADERS = {
    "Accept": "application/vnd.github.raw+json",
}

BCIO_SEARCH_API_PATH = "https://api.bciosearch.org/"
ADDICTO_VOCAB_API_PATH = "https://api.addictovocab.org/"


ENABLE_PLUGINS = True