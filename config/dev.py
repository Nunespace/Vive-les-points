
from .base import *

DEBUG = True

SECRET_KEY = "django-insecure-w4=l$gl&jcbn$((dh-x1afur3(!l-%twsa6wcvav_loi959*f%"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = ["127.0.0.1"]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}
