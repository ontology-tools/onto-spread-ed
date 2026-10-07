import base64


def github_url(full_repository_name: str) -> str:
    return f"https://github.com/{full_repository_name}.git"


def git_env(token: str | None = None, name: str | None = None, email: str | None = None) -> dict[str, str]:
    """
    Environment for git commands against GitHub. The token is passed as HTTP header via environment config, so it is
    never stored in the repository config on disk. `name` and `email` set the author and committer of new commits.
    """
    env = {"GIT_TERMINAL_PROMPT": "0"}

    if token:
        basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
        env |= {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
            "GIT_CONFIG_VALUE_0": f"AUTHORIZATION: basic {basic}",
        }

    if name and email:
        env |= {
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
        }

    return env
