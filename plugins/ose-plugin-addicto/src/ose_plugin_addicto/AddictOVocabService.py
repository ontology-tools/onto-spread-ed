import logging
import os

import aiohttp

from ose_plugin_hbcp.search_api.APIService import APIService
from .AddictOVocabClient import AddictOVocabClient


class AddictOVocabService(APIService[AddictOVocabClient]):
    _logger = logging.getLogger(__name__)

    def __init__(self, prefixes: dict[str, str], session: aiohttp.ClientSession):
        api_client = AddictOVocabClient(
            os.environ.get("OSE_PLUGINS__ADDICTO__API_PATH", "https://api.addictovocab.org/"), session,
            os.environ.get("OSE_PLUGINS__ADDICTO__API_AUTH_TOKEN"),
        )
        super().__init__(prefixes, api_client)

    @property
    def repository_name(self) -> str:
        return "addicto"
