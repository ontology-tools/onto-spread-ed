import logging
import os

import aiohttp

from .APIService import APIService
from .BCIOSearchClient import BCIOSearchClient
from ..services.ConfigurationService import ConfigurationService

PROP_BCIO_SEARCH_API_PATH = "BCIO_SEARCH_API_PATH"
PROP_BCIO_SEARCH_API_AUTH_TOKEN = "BCIO_SEARCH_API_AUTH_TOKEN"


class BCIOSearchService(APIService):
    _api_client: BCIOSearchClient
    _logger = logging.getLogger(__name__)

    def __init__(self, config: ConfigurationService, session: aiohttp.ClientSession):
        path = config.app_config.get(PROP_BCIO_SEARCH_API_PATH, os.environ.get(PROP_BCIO_SEARCH_API_PATH))
        auth_token = config.app_config.get(PROP_BCIO_SEARCH_API_AUTH_TOKEN,
                                           os.environ.get(PROP_BCIO_SEARCH_API_AUTH_TOKEN, None))

        api_client = BCIOSearchClient(path, session, auth_token,
                                      config.app_config.get("ENVIRONMENT", "debug") != "production")

        super().__init__(config, api_client)

    @property
    def repository_name(self):
        return "BCIO"
