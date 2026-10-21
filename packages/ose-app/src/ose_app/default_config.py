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
REPOSITORIES_REPOSITORY_CONFIG_STARTUP_REPOSITORIES_FILE = 'startup-repositories.yaml'
REPOSITORIES_REPOSITORY_CONFIG_BASE_URL = 'repos/{full_name}/contents/{path}'
REPOSITORIES_REPOSITORY_CONFIG_REQUEST_HEADERS = {
    "Accept": "application/vnd.github.raw+json",
}
BCIO_SEARCH_API_PATH = "https://api.bciosearch.org/"
ADDICTO_VOCAB_API_PATH = "https://api.addictovocab.org/"


ENABLE_PLUGINS = True

RELEASE_MAX_PARALLEL = 2
"""Releases the release runner (`flask release-runner`) runs at once, of different repositories"""

RELEASE_POLL_INTERVAL = 2.0
"""Seconds between release request polls."""
RELEASE_HEARTBEAT_INTERVAL = 10.0
"""Seconds between heartbeat updates and stale-runner checks."""
RELEASE_LEASE_TIMEOUT = 60.0
"""Seconds without a heartbeat before another runner may take over a release."""
RELEASE_PROGRESS_INTERVAL = 1.0
"""Minimum seconds between persisted progress updates; zero disables throttling."""
