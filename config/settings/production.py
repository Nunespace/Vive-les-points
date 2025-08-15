# config/settings/production.py
from .base import *  # noqa
import os
import pymysql
from .base import env
from . import BASE_DIR
from pathlib import Path

# DB (o2switch + PyMySQL)
pymysql.install_as_MySQLdb()
DATABASES = {"default": env.db("DJANGO_DATABASE_URL")}
DATABASES["default"]["OPTIONS"] = {
    "charset": "utf8mb4",
    "init_command": "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci', sql_mode='STRICT_TRANS_TABLES'",
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = True

ALLOWED_HOSTS = [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [f"https://{h.strip()}" for h in ALLOWED_HOSTS if h.strip()]

# Le chemin absolu vers le répertoire dans lequel collectstatic rassemble les fichiers statiques en
# vue du déploiement.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#static-root
STATIC_ROOT = Path(
    env("DJANGO_STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
)
MEDIA_ROOT = env.path("DJANGO_MEDIA_ROOT",  default=BASE_DIR / "media")
MEDIA_URL = "/media/"

# Proxy/HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Secure-sessionid"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_NAME = "__Secure-csrftoken"

DEFAULT_HSTS_SECONDS = 60
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", DEFAULT_HSTS_SECONDS))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True)

# Referrer-Policy (nécessite le middleware django_referrer_policy)
REFERRER_POLICY = env("DJANGO_SECURE_REFERRER_POLICY", default="strict-origin-when-cross-origin")

# Emails
EMAIL_CONFIG = env.email("DJANGO_EMAIL_URL", default="consolemail://")
globals().update(**EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="Vive les points <mathieu@vive-les-points.fr>")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[Vive les points] ")

ADMIN_URL = env("DJANGO_ADMIN_URL")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {"handlers": ["mail_admins"], "level": "ERROR", "propagate": True},
        "django.security.DisallowedHost": {"level": "ERROR", "handlers": ["console", "mail_admins"], "propagate": True},
    },
}

