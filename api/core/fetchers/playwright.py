"""
Fetcher Playwright
Navigateur headless pour sites complexes
"""

import time
import logging
from threading import Lock
from config import Config
from playwright.sync_api import sync_playwright
from api.core.utils import is_content_complete

logger = logging.getLogger(__name__)

# Lock pour Playwright (pas thread-safe)
_playwright_lock = Lock()


def fetch_with_playwright(url: str) -> str:
    """
    Récupère le contenu via Playwright (optimisé pour la vitesse)

    Optimisations :
    - Blocage des publicités et trackers
    - Blocage des images, fonts, médias inutiles
    - Désactivation du JavaScript non essentiel
    - Headers anti-détection

    IMPORTANT: Utilise un lock global pour éviter les conflits
    entre threads (Playwright n'est pas thread-safe)

    Args:
        url: URL à récupérer

    Returns:
        HTML du contenu

    Raises:
        Exception: En cas d'erreur
    """

    logger.debug(f"🎭 [3/3] Playwright: {url[:60]}...")
    start = time.time()

    # CRITIQUE: Lock pour éviter "Racing with another loop"
    # Playwright ne peut être utilisé que par un thread à la fois
    with _playwright_lock:
        try:
            with sync_playwright() as p:
                # Lancement du navigateur avec options optimisées
                browser = p.chromium.launch(
                    headless=True,
                    args=Config.PLAYWRIGHT_ARGS,
                )

                context = browser.new_context(
                    user_agent=Config.HEADERS["User-Agent"],
                    viewport={"width": 1920, "height": 1080},
                    # Désactiver JavaScript (si le contenu ne dépend pas de JS)
                    # Décommenter pour encore plus de vitesse :
                    java_script_enabled=False,
                    # Ignorer les erreurs HTTPS
                    ignore_https_errors=True,
                    # Bloquer les images, fonts, médias
                    # (le contenu textuel reste accessible)
                    bypass_csp=True,
                )

                # Bloquer les requêtes inutiles
                def block_aggressively(route, request):
                    """Bloque les pubs, trackers, images, fonts selon la config"""
                    resource_type = request.resource_type
                    request_url = request.url

                    # Bloquer par type de ressource (selon config)
                    if Config.PLAYWRIGHT_BLOCK_IMAGES and resource_type in [
                        "image",
                        "imageset",
                    ]:
                        route.abort()
                        return

                    if Config.PLAYWRIGHT_BLOCK_MEDIA and resource_type in ["media"]:
                        route.abort()
                        return

                    if Config.PLAYWRIGHT_BLOCK_FONTS and resource_type in ["font"]:
                        route.abort()
                        return

                    # Bloquer les CSS (optionnel, garde le contenu)
                    if resource_type in ["stylesheet"]:
                        route.abort()
                        return

                    # Bloquer les domaines de pubs (si activé)
                    if Config.PLAYWRIGHT_BLOCK_ADS:
                        if any(ad in request_url for ad in Config.ADS_DOMAINS):
                            route.abort()
                            return

                    # Bloquer les trackers (si activé)
                    if Config.PLAYWRIGHT_BLOCK_TRACKERS:
                        if any(
                            tracker in request_url
                            for tracker in Config.TRACKERS_DOMAINS
                        ):
                            route.abort()
                            return

                    # Laisser passer les autres requêtes
                    route.continue_()

                # Activer le blocage
                context.route("**/*", block_aggressively)

                page = context.new_page()

                # Définir le timeout depuis la config
                timeout_ms = Config.PLAYWRIGHT_TIMEOUT * 1000
                page.set_default_timeout(timeout_ms)

                # Navigation rapide (wait_until="domcontentloaded" au lieu de "load")
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

                # Attendre que le contenu principal soit chargé
                # (pas besoin d'attendre networkidle pour du texte)
                try:
                    # Attendre un sélecteur commun pour les articles
                    page.wait_for_selector(
                        'article, main, .content, .article, [role="main"]',
                        timeout=5000,
                        state="attached",
                    )
                except:
                    # Si pas trouvé, continuer quand même
                    logger.debug(
                        "⚠️  Sélecteur article non trouvé, utilisation du DOM complet"
                    )

                # Pas besoin de scroll ni d'attente supplémentaire pour du texte
                content = page.content()

                browser.close()

                if not is_content_complete(content, min_length=200):
                    raise ValueError("Contenu Playwright incomplet")

                elapsed = time.time() - start
                logger.info(f"✓ Playwright OK ({elapsed:.1f}s, {len(content):,} car)")

                return content

        except Exception as e:
            elapsed = time.time() - start
            logger.debug(f"✗ Playwright KO ({elapsed:.1f}s): {str(e)[:50]}")
            raise
