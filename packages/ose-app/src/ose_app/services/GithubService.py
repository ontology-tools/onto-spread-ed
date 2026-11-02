import logging
from typing import Optional
from urllib.parse import urlencode

from flask import g, has_app_context
from github import Auth, Github, GithubException
from github.ApplicationOAuth import ApplicationOAuth


class GithubService:
    """
    Creates PyGithub clients and handles the GitHub OAuth web flow.

    `current_client()` acts on behalf of the logged-in user of the current request and is unauthenticated otherwise.
    Long-living services keep this service instead of a client, so that they never use the token of another user.
    """
    _logger = logging.getLogger(__name__)

    def __init__(self, client_id: Optional[str], client_secret: Optional[str]):
        self._client_id = client_id
        self._client_secret = client_secret

    @staticmethod
    def client(access_token: Optional[str] = None) -> Github:
        """Lazy client: objects like repositories are only requested when an attribute needs it"""
        return Github(auth=Auth.Token(access_token) if access_token else None, lazy=True)

    def current_client(self) -> Github:
        """Client with the token of the current request's user, reused for the duration of the request"""
        if not has_app_context():
            return self.client()

        user = g.get("user")
        token = user.github_access_token if user is not None else None
        cached = g.get("_github_client")
        if cached is not None and cached[0] == token:
            return cached[1]

        client = self.client(token)
        g._github_client = (token, client)
        return client

    def _oauth(self) -> ApplicationOAuth:
        if not self._client_id or not self._client_secret:
            raise RuntimeError("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be configured to log in with GitHub")
        return Github().get_oauth_application(self._client_id, self._client_secret)

    def authorize_url(self, scope: str, redirect_uri: Optional[str] = None, state: Optional[str] = None) -> str:
        """The GitHub page that asks the user to authorize this app and then redirects to the OAuth callback"""
        return f"{self._oauth().get_login_url(redirect_uri=redirect_uri, state=state)}&{urlencode({'scope': scope})}"

    def exchange_code(self, code: Optional[str]) -> Optional[str]:
        """The access token for the code passed to the OAuth callback, or None if GitHub refuses it"""
        if not code:
            return None

        try:
            return self._oauth().get_access_token(code).token
        except GithubException as e:
            self._logger.warning(f"Could not get an access token from GitHub: {e}")
            return None
