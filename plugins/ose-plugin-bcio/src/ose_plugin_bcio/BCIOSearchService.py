import logging
import os

import aiohttp

from ose_plugin_hbcp.search_api.APIService import APIService
from .BCIOSearchClient import BCIOSearchClient


class BCIOSearchService(APIService[BCIOSearchClient]):
    _logger = logging.getLogger(__name__)

    def __init__(self, prefixes: dict[str, str], session: aiohttp.ClientSession):
        api_client = BCIOSearchClient(
            os.environ.get("OSE_PLUGINS__BCIO__API_PATH", "https://api.bciosearch.org/"), session,
            os.environ.get("OSE_PLUGINS__BCIO__API_AUTH_TOKEN"),
        )
        super().__init__(prefixes, api_client)

    @property
    def repository_name(self) -> str:
        return "bcio"
