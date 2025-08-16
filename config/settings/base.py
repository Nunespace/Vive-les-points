# config/settings/base.py
import os
import locale
from pathlib import Path
from . import BASE_DIR
from . import env
#import pymysql

#pymysql.install_as_MySQLdb()



# DEBUG:
# De base, on désactive le mode DEBUG pour éviter les oublis en production
# https://docs.djangoproject.com/fr/5.1/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "famille.apps.FamilleConfig",
    "points.apps.PointsConfig",

]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'famille.middleware.SessionDebugMiddleware',
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# MOTS DE PASSE
# Configuration du chiffrement des mots de passe
# https://docs.djangoproject.com/fr/5.1/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # Argon2 n’est pas l’algorithme utilisé par défaut dans Django car il
    # nécessite une bibliothèque tierce (argon2-cffi). Les experts de Password
    # Hashing Competition recommandent cependant l’utilisation immédiate de
    # Argon2 plutôt que les autres algorithmes pris en charge par Django.
    # https://docs.djangoproject.com/fr/5.1/topics/auth/passwords/#using-argon2-with-django
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "unique_user_email.backend.EmailBackend",
]

UNIQUE_USER_EMAIL = True
AUTH_USER_MODEL = "auth.User"

LOGIN_URL = "famille:login"               # (par nom de route)
LOGIN_REDIRECT_URL = "points:dashboard"          # où on atterrit après login
LOGOUT_REDIRECT_URL = "famille:login"

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

USE_THOUSAND_SEPARATOR = True

# Formate les dates en français et en UTF-8 (ex: pour que le é de décembre s'affiche correctement)
locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

# FICHIERS STATIQUES ET MEDIA (CSS, JavaScript, Images)
# Les sites Web ont généralement besoin de servir des fichiers supplémentaires
# tels que des images, du JavaScript ou du CSS. Dans Django, ces fichiers
# sont appelés « fichiers statiques ». Django met à disposition l'app
# django.contrib.staticfiles pour vous assister dans cette gestion.
# https://docs.djangoproject.com/fr/5.1/howto/static-files/

# Le chemin absolu vers le répertoire dans lequel collectstatic rassemble les fichiers statiques en
# vue du déploiement.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#static-root
STATIC_ROOT = Path(
    env("DJANGO_STATIC_ROOT", default=str(BASE_DIR / "staticfiles"))
)

# URL utilisée pour se référer aux fichiers statiques se trouvant dans
# STATIC_ROOT.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#static-url
STATIC_URL = "/static/"

# Ce réglage définit les emplacements supplémentaires que l’application
# staticfiles parcourt. Cela permet de servir des fichiers statiques à partir
# de plusieurs emplacements pour le développement (facultatif)
# https://docs.djangoproject.com/fr/5.1/ref/settings/#staticfiles-dirs
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# La configuration STORAGES définit les backends de stockage pour les fichiers
# par défaut et les fichiers statiques dans une application Django.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#storages
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Liste des moteurs de découverte sachant retrouver les fichiers statiques
# en divers endroits.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# FICHIERS DE MEDIA

# Chemin absolu de répertoire pointant vers le répertoire qui contiendra les
# fichiers uploadés par les utilisateurs.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#media-root
MEDIA_ROOT = Path(env("DJANGO_MEDIA_ROOT", default=str(BASE_DIR / "media")))

# URL qui gère les fichiers médias servis à partir de MEDIA_ROOT, utilisée pour
# la gestion des fichiers stockés. Elle doit se terminer par une barre oblique
# si elle ne contient pas de valeur vide.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#media-url
MEDIA_URL = "/media/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# SECURITE
# Indique si le drapeau HttpOnly doit être utilisé sur le cookie de session.
# Si ce paramètre est défini à True, le code JavaScript côté client ne sera
# pas en mesure d’accéder au cookie de session.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True

# Indique si le drapeau HttpOnly doit être utilisé sur le cookie CSRF. Si ce
# paramètre est défini à True, le JavaScript côté client ne sera pas en mesure
# d’accéder au cookie CSRF.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False

# Ferme la session lorsque le navigateur est fermé
# réf. : https://docs.djangoproject.com/fr/5.1/topics/http/sessions/#browser-length-sessions-vs-persistent-sessions
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Durée de vie des cookies de session en secondes
# Réf. : https://docs.djangoproject.com/fr/5.1/ref/settings/#session-cookie-age
SESSION_COOKIE_AGE = 60 * 60 * 24  # 1 jour

# Valeur par défaut de l’en-tête X-Frame-Options utilisé par
# XFrameOptionsMiddleware pour se protéger contre le
# détournement de click (clickjacking)
# https://docs.djangoproject.com/fr/5.1/ref/settings/#x-frame-options
# L'option "SAMEORIGIN" permet de restreindre le chargement de la page dans un iframe
# uniquement si l'origine de la requête est la même que celle de la page.
X_FRAME_OPTIONS = "SAMEORIGIN"


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Qui reçoit les erreurs serveur (500) par email
ADMINS = [("Mathieu Cazenave", "nunespace@gmail.com")]
MANAGERS = ADMINS


# Expéditeur et préfixe des sujets
SERVER_EMAIL = "errors@dgpython.fr"          # From des mails d’erreurs
DEFAULT_FROM_EMAIL = "no-reply@dgpython.fr"  # From par défaut de ton site
EMAIL_SUBJECT_PREFIX = "[Vive les Points] "

# Backend email (exemple SMTP générique — remplace par ton fournisseur)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.ton-fournisseur.tld"
EMAIL_PORT = 587
EMAIL_HOST_USER = "no-reply@dgpython.fr"
EMAIL_HOST_PASSWORD = "********"
EMAIL_USE_TLS = True

MIDDLEWARE += ["django.middleware.common.BrokenLinkEmailsMiddleware"]

# Évite le spam (favicon, robots, etc.)
import re
IGNORABLE_404_URLS = [
    re.compile(r"^/favicon\.ico$"),
    re.compile(r"^/robots\.txt$"),
    re.compile(r"^/apple-touch-icon.*\.png$"),
    re.compile(r"^/\.well-known/.*$"),
]


env.read_env(BASE_DIR / ".env")

DJANGO_LOG_LEVEL = env("DJANGO_LOG_LEVEL", default="INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    # N’envoie des mails que si DEBUG=False
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },

    "handlers": {
        # Console partout (dev et prod)
        "console": {
            "class": "logging.StreamHandler",
        },
        # Emails aux ADMINS pour erreurs HTTP 500 en prod
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },

    # Niveau par défaut
    "root": {
        "handlers": ["console"],
        "level": DJANGO_LOG_LEVEL,
    },

    "loggers": {
        # Erreurs de requêtes (500) => mail + console
        "django.request": {
            "handlers": ["mail_admins", "console"],
            "level": "ERROR",
            "propagate": False,
        },

        # Tes apps : simple et lisible
        "famille": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
        "points": {
            "handlers": ["console"],
            "level": DJANGO_LOG_LEVEL,
            "propagate": False,
        },
    },
}