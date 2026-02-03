import time
import logging
import requests

from config import Config
from api.core.utils import markdown_to_html, is_content_complete

logger = logging.getLogger(__name__)

def fetch_with_jina(url: str) -> str:
    """
    Récupère le contenu via Jina.ai
    
    Args:
        url: URL à récupérer
        
    Returns:
        HTML du contenu
        
    Raises:
        Exception: En cas d'erreur
    """
    logger.debug(f"📥 [1/3] Jina: {url[:60]}...")
    start = time.time()
    
    try:
        jina_url = f"{Config.JINA_BASE_URL}/{url}"
        session = requests.Session()
        session.headers.update(Config.JINA_HEADERS)
        
        response = session.get(
            jina_url, 
            timeout=Config.JINA_TIMEOUT, 
            allow_redirects=True
        )
        response.raise_for_status()
        
        markdown_content = response.text
        
        if len(markdown_content) < 100:
            raise ValueError("Contenu Jina trop court")
        
        html = markdown_to_html(markdown_content)
        
        if not is_content_complete(html, Config.MIN_CONTENT_LENGTH):
            raise ValueError("Contenu Jina incomplet")
        
        elapsed = time.time() - start
        logger.info(f"✓ Jina OK ({elapsed:.1f}s, {len(html):,} car)")
        
        return html
        
    except Exception as e:
        elapsed = time.time() - start
        logger.debug(f"✗ Jina KO ({elapsed:.1f}s): {str(e)[:50]}")
        raise
