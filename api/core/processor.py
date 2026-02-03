"""
Traitement des entrées de flux RSS
"""

import re
import logging
from datetime import datetime
from typing import Any, Dict, Optional
import hashlib
from api.core.utils import clean_html
from api.core.fetchers.fetchers import fetch_content_cascade
from api.core.extractors import extract_article_content, extract_images, extract_tags

logger = logging.getLogger(__name__)


def process_entry(
    entry: Any, entry_num: int, total: int, preferred_method: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Traite une entrée de flux RSS

    Args:
        entry: Entrée du flux RSS
        entry_num: Numéro de l'entrée
        total: Nombre total d'entrées

    Returns:
        Dictionnaire avec les données traitées ou None
    """
    try:
        title = entry.get("title", "Sans titre")
        link = entry.get("link", "")

        if not link:
            logger.warning(f"[{entry_num}/{total}] Pas de lien pour: {title[:40]}")
            return None

        logger.debug(f"[{entry_num}/{total}] {title[:50]}...")

        # Récupérer les catégories du flux RSS
        rss_categories = []
        if hasattr(entry, "tags"):
            rss_categories = [tag.term for tag in entry.tags if hasattr(tag, "term")]

        # Récupération du contenu
        try:
            # Récupérer le HTML brut
            raw_html = fetch_content_cascade(link, preferred_method)

            if not raw_html:
                raise ValueError("Aucune méthode n'a réussi")

            # Extraire le contenu principal
            content = extract_article_content(raw_html)

            # Extraire les images
            images = extract_images(raw_html, link)

            # Extraire les tags
            article_tags = extract_tags(raw_html, rss_categories)

            method_used = "cascade"

            text_length = len(re.sub(r"<[^>]+>", "", content))
            logger.debug(
                f"[{entry_num}/{total}] ✓ OK: {text_length} car, "
                f"{len(article_tags)} tags, "
                f"image: {'✓' if images.get('article_image') else '✗'}"
            )

        except Exception as e:
            # Fallback: résumé RSS
            raw_summary = entry.get("summary", entry.get("description", ""))

            if raw_summary and len(raw_summary) > 50:
                content = raw_summary if "<" in raw_summary else f"<p>{raw_summary}</p>"
                method_used = "rss_summary"
            else:
                content = "<p>Contenu non disponible</p>"
                method_used = "unavailable"

            images = {"article_image": None, "site_logo": None, "favicon": None}
            article_tags = rss_categories

            logger.warning(f"[{entry_num}/{total}] ⚠️  Fallback: {str(e)[:50]}")

        # Nettoyer le contenu
        content = clean_html(content)

        # Extraire la date
        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                pub_date = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError) as e:
                logger.debug(f"[{entry_num}/{total}] Date invalide: {e}")

        # Générer un ID unique
        entry_id = hashlib.sha256(link.encode()).hexdigest()

        return {
            "id": entry_id,
            "title": title,
            "link": link,
            "content": content,
            "pub_date": pub_date,
            "images": images,
            "tags": article_tags,
            "method": method_used,
        }

    except Exception as e:
        logger.error(f"[{entry_num}/{total}] ✗ Erreur critique: {str(e)[:100]}")
        return None
