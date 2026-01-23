from .release import bp as release
from .validate import bp as validate
from .repos import bp as repos
from .external import bp as external
from .search import bp as search
from .edit import bp as edit
from .scripts import bp as scripts
from .settings import bp as settings
from .visualise import bp as visualise
from .plugins import bp as plugins

blueprints = [
    release,
    validate,
    repos,
    external,
    search,
    edit,
    scripts,
    settings,
    visualise,
    plugins
]
