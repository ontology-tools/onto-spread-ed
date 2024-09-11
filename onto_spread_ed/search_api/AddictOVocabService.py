import logging
import os

import aiohttp

from .APIService import APIService
from .AddictOVocabClient import AddictOVocabClient

PROP_ADDICTO_VOCAB_API_PATH = "PROP_ADDICTO_VOCAB_API_PATH"
PROP_ADDICTO_VOCAB_API_AUTH_TOKEN = "PROP_ADDICTO_VOCAB_API_AUTH_TOKEN"


class AddictOVocabService(APIService):
    _logger = logging.getLogger(__name__)

    def __init__(self, config: dict, session: aiohttp.ClientSession):
        path = config.get(PROP_ADDICTO_VOCAB_API_PATH)
        auth_token = config.get(PROP_ADDICTO_VOCAB_API_AUTH_TOKEN,
                                os.environ.get(PROP_ADDICTO_VOCAB_API_AUTH_TOKEN, None))

        api_client = AddictOVocabClient(path, session, auth_token, config.get("DEBUG", False))

        super().__init__(config, api_client)
