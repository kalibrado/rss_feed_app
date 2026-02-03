"""
Module de récupération de contenu
Auto-découverte des fetchers
"""

# Import des fetchers individuels
from .jina import fetch_with_jina
from .cloudscraper import fetch_with_cloudscraper
from .playwright import fetch_with_playwright

# Optionnel: Import automatique de tous les fetchers custom
# Permet d'ajouter de nouveaux fetchers sans modifier ce fichier
__all__ = [
    'fetch_with_jina',
    'fetch_with_cloudscraper', 
    'fetch_with_playwright',
]

