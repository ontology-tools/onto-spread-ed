import re


def css_safe(s: str) -> str:
    return re.sub("[^0-9a-zA-Z]", "_", s)
