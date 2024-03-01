from .release import bp as release
from .validate import bp as validate
from .repos import bp as repos
from .external import bp as external

blueprints = [
    release,
    validate,
    repos,
    external
]
