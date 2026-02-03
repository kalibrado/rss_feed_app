"""
Méthodes de récupération de contenu cloudscraper
"""
import time
import logging
import cloudscraper

from config import Config
from api.core.utils import  is_content_complete



logger = logging.getLogger(__name__)


def fetch_with_cloudscraper(url: str) -> str:
    """
    Récupère le contenu via cloudscraper
    
    Args:
        url: URL à récupérer
        
    Returns:
        HTML du contenu
        
    Raises:
        Exception: En cas d'erreur
    """

    
    logger.debug(f"☁️  [2/3] cloudscraper: {url[:60]}...")
    start = time.time()
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome', 
                'platform': 'linux', 
                'mobile': True
            }
        )
        
        response = scraper.get(url, timeout=Config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        html = response.text
        
        if not is_content_complete(html, min_length=200):
            raise ValueError("Contenu cloudscraper incomplet")
        
        elapsed = time.time() - start
        logger.info(f"✓ cloudscraper OK ({elapsed:.1f}s, {len(html):,} car)")
        
        return html
        
    except Exception as e:
        elapsed = time.time() - start
        logger.debug(f"✗ cloudscraper KO ({elapsed:.1f}s): {str(e)[:50]}")
        raise

