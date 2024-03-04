from .release import bp as release
from .validate import bp as validate
from .repos import bp as repos
from .external import bp as external
from .search import bp as search
from .edit import bp as edit

blueprints = [
    release,
    validate,
    repos,
    external,
    search,
    edit
]
