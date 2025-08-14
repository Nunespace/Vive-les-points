
from .base import *
import os
import pymysql
from .base import *  # noqa: F403
from .base import INSTALLED_APPS
from .base import MIDDLEWARE
from .base import env
from config.env_validators import validate_commune_databases

# Valider les configurations du .env pour les bases multi-communes
# validate_commune_databases()

import os

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

DATABASES = {"default": env.db("DJANGO_DATABASE_URL")}

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# o2switch ne supporte pas mysqlclient: nous utilisons un driver pur python
# qui sait se faire passer pour MySQLclient
pymysql.install_as_MySQLdb()

# Settings recommandés pour l'usage de mysql et mariadb avec django
DATABASES["default"]["OPTIONS"] = {
    "charset": "utf8mb4",
    "init_command": "SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci', sql_mode='STRICT_TRANS_TABLES'",
}

# SECURITE
# La variable SECURE_PROXY_SSL_HEADER est utilisée dans Django pour indiquer
# que l'application est derrière un proxy inverse (comme Nginx ou un load
# balancer) qui gère le protocole SSL. En définissant
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https"), on spécifie à
# Django de considérer les requêtes avec l'en-tête HTTP_X_FORWARDED_PROTO comme
# sécurisées si elles sont marquées avec la valeur "https".
# Cela permet à Django de traiter correctement ces requêtes comme étant faites
# via HTTPS, même si la connexion entre Django et le proxy est en HTTP.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# La variable SECURE_SSL_REDIRECT configure Django pour rediriger
# automatiquement toutes les requêtes HTTP vers HTTPS
# https://docs.djangoproject.com/fr/5.1/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

# La variable SESSION_COOKIE_SECURE = True garantit que les cookies de session
# ne sont envoyés que via des connexions HTTPS, renforçant ainsi la sécurité en
# empêchant leur transmission sur des connexions non sécurisées.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True

# La variable SESSION_COOKIE_NAME = "__Secure-sessionid" permet de définir un
# nom personnalisé pour le cookie de session, et le préfixe __Secure- est
# souvent utilisé pour indiquer que ce cookie doit être envoyé uniquement sur
# des connexions HTTPS.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#session-cookie-name
SESSION_COOKIE_NAME = "__Secure-sessionid"

# La variable CSRF_COOKIE_SECURE = True garantit que le cookie CSRF (utilisé
# pour protéger contre les attaques CSRF) n'est transmis que via des connexions
# HTTPS, renforçant ainsi la sécurité des requêtes contre les attaques sur des
# connexions non sécurisées.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True

# La variable CSRF_COOKIE_NAME = "__Secure-csrftoken" personnalise le nom du
# cookie CSRF, et le préfixe __Secure- est utilisé pour indiquer que le cookie
# doit être envoyé uniquement sur des connexions HTTPS, conformément aux
# meilleures pratiques de sécurité pour les cookies sensibles.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#csrf-cookie-name
CSRF_COOKIE_NAME = "__Secure-csrftoken"

# La variable SECURE_HSTS_SECONDS = 60 active la politique HTTP Strict
# Transport Security (HSTS) pour 60 secondes, demandant aux navigateurs
# d'utiliser exclusivement des connexions HTTPS pour le site pendant cette
# durée, renforçant ainsi la sécurité en empêchant les dégradations vers HTTP.
# https://docs.djangoproject.com/fr/5.1/topics/security/#ssl-https
# https://docs.djangoproject.com/fr/5.1/ref/settings/#secure-hsts-seconds
# TODO: Réglez d'abord cette valeur à 60 secondes, puis à 518400 une fois que
# vous aurez prouvé que la première fonctionne.
DEFAULT_HSTS_SECONDS = 60  # 60 s
SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_SECURE_HSTS_SECONDS", DEFAULT_HSTS_SECONDS),
)  # noqa

# La variable SECURE_HSTS_INCLUDE_SUBDOMAINS indique si la politique HSTS
# (HTTP Strict Transport Security) doit s'appliquer également à tous les
# sous-domaines du site. En la configurant avec une variable d'environnement,
# ici par défaut à True, elle garantit que toutes les requêtes vers les
# sous-domaines doivent aussi être forcées à utiliser HTTPS, renforçant ainsi
# la sécurité à l'échelle de l'ensemble du domaine.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)

# La variable SECURE_HSTS_PRELOAD, lorsqu'elle vaut True, permet au domaine
# d'être inscrit dans la liste de préchargement HSTS. Cela signifie que les
# navigateurs qui supportent cette fonctionnalité refuseront toute connexion
# HTTP dès la première visite, renforçant ainsi la sécurité en évitant les
# attaques avant même la première requête HTTP non sécurisée.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)

# La variable SECURE_CONTENT_TYPE_NOSNIFF, activée ici par défaut via une
# variable d'environnement, permet d'ajouter l'en-tête HTTP
# X-Content-Type-Options: nosniff aux réponses. Cet en-tête empêche les
# navigateurs de deviner le type de contenu et de le traiter différemment de
# celui spécifié, ce qui renforce la sécurité en empêchant certaines attaques,
# comme celles liées aux types de fichiers mal interprétés (MIME type sniffing).
# https://docs.djangoproject.com/fr/5.1/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)

# Active ou désactive l'en-tête HTTP "X-XSS-Protection".
# Cet en-tête est utilisé pour activer le filtre XSS dans certains navigateurs.
# Lorsque activé, le navigateur bloquera l'affichage de la page si une attaque XSS est détectée.
# C'est une mesure de sécurité supplémentaire contre les attaques XSS.
# Note : Cette protection est surtout pertinente pour les navigateurs plus anciens,
# car les navigateurs modernes tendent à abandonner ce mécanisme au profit d'autres protections.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = env.bool(
    "DJANGO_SECURE_BROWSER_XSS_FILTER",
    default=True,
)

# Referrer-policy
# Cette configuration définit la politique d'envoi de l'en-tête "Referrer-Policy"
# dans les réponses HTTP. Cet en-tête contrôle les informations du "Referer"
# (l'URL de la page précédente) qui seront transmises à un site lorsque
# l'utilisateur suit un lien ou fait une requête.
#
# La valeur "no-referrer-when-downgrade" signifie que le "Referer" sera envoyé
# uniquement si la requête de destination utilise le même protocole ou un protocole plus sécurisé.
# Par exemple, il sera transmis lors de la navigation de HTTPS vers HTTPS,
# mais pas de HTTPS vers HTTP (ce qui pourrait être moins sûr).
# Cette politique permet de protéger les informations sensibles tout en maintenant une compatibilité de base.
# https://django-referrer-policy.readthedocs.io/en/1.0/
REFERRER_POLICY = os.environ.get(  # noqa
    "DJANGO_SECURE_REFERRER_POLICY", "no-referrer-when-downgrade"
).strip()

# EMAIL
# Configuration de l'email. Par défaut, les courriels sont affichés dans le
# le terminal.
# Pour définir un back-end d'envoi d'emails, définir la variable d'environnement
# DJANGO_EMAIL_URL avec les valeurs suivantes:
# - SMTP avec SSL: smtp+ssl://USER:PASSWORD@HOST:PORT
# - SMTP avec STARTTLS: smtp+tls://USER:PASSWORD@HOST:PORT
# - Console: consolemail://
# https://docs.djangoproject.com/fr/5.1/ref/settings/
# EMAIL_CONFIG = env.email("DJANGO_EMAIL_URL",default="consolemail://",)
# globals().update(**EMAIL_CONFIG)

# La variable DEFAULT_FROM_EMAIL définit l'adresse email par défaut utilisée
# par Django pour envoyer des emails depuis l'application.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#default-from-email
DEFAULT_FROM_EMAIL = env(
    "DJANGO_DEFAULT_FROM_EMAIL",
    default="dgpython <noreply@dgpython.fr>",
)

# La variable SERVER_EMAIL définit l'adresse email utilisée pour envoyer des
# messages d'erreur ou d'alerte émanant du serveur Django, comme les
# notifications d'erreurs 500.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#server-email
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", default=DEFAULT_FROM_EMAIL)

# La variable EMAIL_SUBJECT_PREFIX ajoute un préfixe personnalisé aux sujets de
# tous les emails envoyés par l'application Django.
# https://docs.djangoproject.com/fr/5.1/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = env(
    "DJANGO_EMAIL_SUBJECT_PREFIX",
    default="[dgpython] ",
)

# ADMIN
# La variable ADMIN_URL définit l'URL personnalisée pour accéder à l'interface
# d'administration Django. En la configurant via une variable d'environnement,
# cela permet de masquer ou de rendre l'URL de l'administration moins
# prévisible (au lieu de l'URL par défaut /admin/), améliorant ainsi la
# sécurité en réduisant le risque d'attaques automatisées sur l'interface
# d'administration.
# ou DJANGO_ADMIN_URL?
ADMIN_URL = env("DJANGO_ADMIN_URL")


# Journalisation
# https://docs.djangoproject.com/fr/5.1/ref/settings/#logging
# Voir https://docs.djangoproject.com/fr/5.1/topics/logging/
# pour plus de détails sur la personnalisation de la configuration du logging.
# Un exemple de configuration de logging. La seule action de logging
# concrète effectuée par cette configuration est d'envoyer un email
# aux administrateurs du site pour chaque erreur HTTP 500 lorsque DEBUG=False.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
    },
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
        "sentry_sdk": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
