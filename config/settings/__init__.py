# config/settings/__init__.py
from pathlib import Path

import environ  # pour aller lire variables d'environnement

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")
