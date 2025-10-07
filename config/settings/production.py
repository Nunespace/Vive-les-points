# config/settings/production.py
from .base import *  # noqa
from .base import env

import os
import logging
from urllib.parse import urlparse

import pymysql
import sentry_sdk
from django.core.exceptions import DisallowedHost
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


# --- DB (o2switch + PyMySQL) ------------------------------------------------
pymysql.install_as_MySQLdb()

DATABASES = {"default": env.db("DJANGO_DATABASE_URL")}
DATABASES["default"]["OPTIONS"] = {
    "charset": "utf8mb4",
    "init_command": "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci', sql_mode='STRICT_TRANS_TABLES'",
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

# --- Sécurité / hôtes -------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["vive-les-points.fr", "www.vive-les-points.fr"],
)
if not ALLOWED_HOSTS:
    raise Exception("DJANGO_ALLOWED_HOSTS n'est pas défini dans l'environnement !")

CSRF_TRUSTED_ORIGINS = [
    "https://vive-les-points.fr",
    "https://www.vive-les-points.fr",
]

# Proxy/HTTPS (o2switch/Reverse proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

SESSION_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Secure-sessionid"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_NAME = "__Secure-csrftoken"

# HSTS (active si HTTPS est bien en place)
DEFAULT_HSTS_SECONDS = 518400  # 6 jours (augmente progressivement si besoin)
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", DEFAULT_HSTS_SECONDS))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = env.bool("DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=True)

# (Optionnel) Referrer-Policy — nécessite le middleware django-referrer-policy
REFERRER_POLICY = os.environ.get("DJANGO_SECURE_REFERRER_POLICY", "no-referrer-when-downgrade").strip()

# ⚠️ Supprimé en Django 4+: SECURE_BROWSER_XSS_FILTER n'a plus d'effet → on ne le définit pas.

# --- Canonical host ---------------------------------------------------------
CANONICAL_HOST = env("CANONICAL_HOST", default="vive-les-points.fr")  # ou "www.vive-les-points.fr"
CANONICAL_FORCE_HTTPS = env.bool("CANONICAL_FORCE_HTTPS", default=True)

# Insère le middleware juste après SecurityMiddleware
MIDDLEWARE = list(MIDDLEWARE)
try:
    sec_idx = MIDDLEWARE.index("django.middleware.security.SecurityMiddleware")
except ValueError:
    sec_idx = 0
MIDDLEWARE.insert(sec_idx + 1, "config.middleware.CanonicalHostMiddleware")


# --- Emails -----------------------------------------------------------------
EMAIL_CONFIG = env.email("DJANGO_EMAIL_URL", default="consolemail://")
globals().update(**EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", default="Vive les points <mathieu@vive-les-points.fr>")
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = env("DJANGO_EMAIL_SUBJECT_PREFIX", default="[Vive les points] ")

ADMIN_URL = env("DJANGO_ADMIN_URL")

# --- Clickjacking -----------------------------------------------------------
X_FRAME_OPTIONS = "DENY"

# --- LOGGING ----------------------------------------------------------------
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
        "console": {"level": "INFO", "class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {"handlers": ["mail_admins"], "level": "ERROR", "propagate": True},
        "django.security.DisallowedHost": {"level": "ERROR", "handlers": ["console"], "propagate": True},
    },
}

# --- SENTRY -----------------------------------------------------------------
def _sentry_before_send(event, hint):
    # 1) Bruit : DisallowedHost
    exc = hint.get("exc_info")
    if exc:
        _, exc_value, _ = exc
        if isinstance(exc_value, DisallowedHost):
            return None

    # 2) Chemins bots très courants
    try:
        req = event.get("request", {})
        url = req.get("url", "")
        path = urlparse(url).path
        bot_paths = (
            "/wp-login.php", "/wp-content", "/xmlrpc.php", "/.env", "/.git",
            "/admin.php", "/phpmyadmin", "/etc/passwd", "/vendor/phpunit",
            "/wp-includes", "/sitemap.xml.gz",
        )
        if any(p in path for p in bot_paths):
            return None
    except Exception:
        pass

    return event


SENTRY_DSN = env("SENTRY_DSN", default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
        environment=env("SENTRY_ENV", default="production"),
        release=env("SENTRY_RELEASE", default=None),
        send_default_pii=False,  # RGPD
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
        profiles_sample_rate=env.float("SENTRY_PROFILES_SAMPLE_RATE", default=0.0),
        before_send=_sentry_before_send,
    )

MAINTENANCE_MODE = True
