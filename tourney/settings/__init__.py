from .default_settings import *  # NOQA
from .tourney_settings import *  # NOQA

try:
    from .local_settings import *  # NOQA
except ImportError:
    pass
