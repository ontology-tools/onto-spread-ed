import logging
import os

import aiohttp

from .APIService import APIService
from .AddictOVocabClient import AddictOVocabClient
from ..services.ConfigurationService import ConfigurationService

PROP_ADDICTO_VOCAB_API_PATH = "ADDICTO_VOCAB_API_PATH"
PROP_ADDICTO_VOCAB_API_AUTH_TOKEN = "ADDICTO_VOCAB_API_AUTH_TOKEN"


class AddictOVocabService(APIService):
    @property
    def repository_name(self) -> str:
        return "AddictO"

    _logger = logging.getLogger(__name__)

    def __init__(self, config: ConfigurationService, session: aiohttp.ClientSession):
        path = config.app_config.get(PROP_ADDICTO_VOCAB_API_PATH, os.environ.get(PROP_ADDICTO_VOCAB_API_PATH))
        auth_token = config.app_config.get(PROP_ADDICTO_VOCAB_API_AUTH_TOKEN,
                                          os.environ.get(PROP_ADDICTO_VOCAB_API_AUTH_TOKEN, None))

        api_client = AddictOVocabClient(path, session, auth_token, config.app_config.get("DEBUG", False))

        super().__init__(config, api_client)
