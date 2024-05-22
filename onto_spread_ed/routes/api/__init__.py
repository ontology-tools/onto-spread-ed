from .release import bp as release
from .validate import bp as validate
from .repos import bp as repos
from .external import bp as external
from .search import bp as search
from .edit import bp as edit
from .scripts import bp as scripts

blueprints = [
    release,
    validate,
    repos,
    external,
    search,
    edit,
    scripts
]
