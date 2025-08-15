# config/settings/dev.py
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import env
from .base import DATABASES
from . import BASE_DIR


DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="Lt6DO1LFhlkwizCJEf-3Tp76EUJfIsHl2tkFAiNIyOI",
)

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
INTERNAL_IPS = ["127.0.0.1"]



# Ce dictionnaire contient toutes les autres options de configuration de
# Django-Debug-Toolbar. Certaines s'appliquent à la barre d'outils elle-même,
# d'autres sont spécifiques à certains panneaux.
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # Désactive le panneau de profilage à cause d'un problème avec Python 3.12:
        # https://github.com/jazzband/django-debug-toolbar/issues/1875
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}