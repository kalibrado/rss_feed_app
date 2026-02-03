"""
Configuration de l'application RSS Feed Filter
"""

import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée"""

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    APP_ENV= os.getenv("APP_ENV", "development")
    # API
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))

    # Performance
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    JINA_TIMEOUT = int(os.getenv("JINA_TIMEOUT", "30"))

    # Limites
    MAX_FEED_ENTRIES = int(os.getenv("MAX_FEED_ENTRIES", "1000"))
    MIN_CONTENT_LENGTH = int(os.getenv("MIN_CONTENT_LENGTH", "50"))
    MAX_TAGS_PER_ARTICLE = int(os.getenv("MAX_TAGS_PER_ARTICLE", "10"))
    MAX_FEED_ENTRIES = int(os.getenv("MAX_FEED_ENTRIES", "200"))

    # URLs
    JINA_BASE_URL = os.getenv("JINA_BASE_URL", "https://r.jina.ai")

    # Features
    USE_JINA = os.getenv("USE_JINA", "true").lower() == "true"
    USE_CLOUDSCRAPER = os.getenv("USE_CLOUDSCRAPER", "true").lower() == "true"
    USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "true").lower() == "true"

    # Playwright settings
    PLAYWRIGHT_BLOCK_IMAGES = (
        os.getenv("PLAYWRIGHT_BLOCK_IMAGES", "true").lower() == "true"
    )
    PLAYWRIGHT_BLOCK_ADS = os.getenv("PLAYWRIGHT_BLOCK_ADS", "true").lower() == "true"
    PLAYWRIGHT_BLOCK_TRACKERS = (
        os.getenv("PLAYWRIGHT_BLOCK_TRACKERS", "true").lower() == "true"
    )
    PLAYWRIGHT_TIMEOUT = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30"))
    PLAYWRIGHT_BLOCK_MEDIA = (
        os.getenv("PLAYWRIGHT_BLOCK_MEDIA", "true").lower() == "true"
    )
    PLAYWRIGHT_BLOCK_FONTS = (
        os.getenv("PLAYWRIGHT_BLOCK_FONTS", "true").lower() == "true"
    )
    PLAYWRIGHT_ARGS = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
        "--disable-extensions",
        "--disable-plugins",
        "--disable-images",  # Désactiver les images pour plus de vitesse
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--disable-dev-tools",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-breakpad",
        "--disable-component-extensions-with-background-pages",
        "--disable-features=TranslateUI,BlinkGenPropertyTrees",
        "--disable-ipc-flooding-protection",
        "--disable-renderer-backgrounding",
        "--enable-features=NetworkService,NetworkServiceInProcess",
        "--force-color-profile=srgb",
        "--hide-scrollbars",
        "--metrics-recording-only",
        "--mute-audio",
    ]
    # Headers HTTP
    HEADERS: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    }
    # Headers spécifiques Jina
    JINA_HEADERS: Dict[str, str] = {
        "X-Return-Format": "html",
        "X-With-Generated-Alt": "true",
        "X-With-Images-Summary": "true",
        "X-Timeout": str(JINA_TIMEOUT),
        **HEADERS,
    }
    BAD_KEYWORDS = [
        "cookie",
        "consent",
        "gdpr",
        "privacy",
        "advert",
        "ads",
        "pub",
        "sponsor",
        "promo",
        "banner",
        "social",
        "share",
        "follow",
        "newsletter",
        "subscribe",
        "footer",
        "header",
        "nav",
        "sidebar",
        "recommend",
        "related",
        "suggest",
        "comment",
        "comments",
        "commentaire",
        "commentaires",
        "responses",
        "reply",
        "discussion",
        "disqus",
        "fb-comments",
        "facebook-comments",
    ]
    ADS_DOMAINS = [
        "doubleclick.net",
        "googlesyndication.com",
        "googleadservices.com",
        "adnxs.com",
        "advertising.com",
        "adsystem.com",
        "adtech.de",
        "criteo.com",
        "outbrain.com",
        "taboola.com",
        "pubmatic.com",
        "casalemedia.com",
        "rubiconproject.com",
        "openx.net",
    ]
    TRACKERS_DOMAINS = [
        "google-analytics.com",
        "googletagmanager.com",
        "analytics.google.com",
        "facebook.com/tr",
        "connect.facebook.net",
        "pixel.facebook.com",
        "mixpanel.com",
        "segment.com",
        "amplitude.com",
        "hotjar.com",
        "mouseflow.com",
        "crazyegg.com",
        "quantserve.com",
        "scorecardresearch.com",
        "chartbeat.com",
        "newrelic.com",
    ]
