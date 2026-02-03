"""
Méthodes de récupération de contenu
"""
import logging
from typing import Optional
from config import Config
from . import fetch_with_playwright, fetch_with_jina, fetch_with_cloudscraper

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False

FETCH_METHODS = {
    "playwright": {
        "label": "Playwright",
        "func": fetch_with_playwright,
        "enabled": lambda: Config.USE_PLAYWRIGHT and PLAYWRIGHT_AVAILABLE,
    },
    "jina": {
        "label": "Jina",
        "func": fetch_with_jina,
        "enabled": lambda: Config.USE_JINA,
    },
    "cloudscraper": {
        "label": "cloudscraper",
        "func": fetch_with_cloudscraper,
        "enabled": lambda: Config.USE_CLOUDSCRAPER and CLOUDSCRAPER_AVAILABLE,
    },
}


def fetch_content_cascade(url: str, preferred_method: str | None) -> Optional[str]:
    methods = []

    if preferred_method:
        key = preferred_method.lower()
        method = FETCH_METHODS.get(key)
        if method:
            methods.append(method)
    else:
        for method in FETCH_METHODS.values():
            if method["enabled"]():
                methods.append(method)
            else:
                logger.debug(f"⚠️  Méthode {method['label']} désactivée ou non disponible")

    if not methods:
        raise RuntimeError("Aucune méthode de récupération activée")

    logger.debug(
        "🔄 Méthodes à tester: %s",
        [m["label"] for m in methods]
    )

    for method in methods:
        try:
            return method["func"](url)
        except Exception as e:
            logger.debug(
                "❌ %s a échoué: %s",
                method["label"],
                e
            )
    logger.error("Toutes les méthodes de récupération ont échoué")
    return None