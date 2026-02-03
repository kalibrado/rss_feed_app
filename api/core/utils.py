"""
Fonctions utilitaires
"""

import re
import markdown
from functools import lru_cache
from urllib.parse import urljoin
from typing import Optional
import logging
import tldextract
from html import unescape
from datetime import timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def ensure_utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def sanitize_html(html: str, bad_keywords: dict) -> str:
    html = unescape(html)
    soup = BeautifulSoup(html, "html.parser")

    # Supprime les tags contenant les mots-clés
    for tag in soup.find_all(True):
        tag_text = " ".join(tag.get_text(strip=True).lower().split())
        if any(k in tag_text for k in bad_keywords):
            tag.decompose()

    return str(soup)


def get_site_name(url: str) -> str:
    ext = tldextract.extract(url)
    return ext.domain


@lru_cache(maxsize=200)
def markdown_to_html(markdown_text: str) -> str:
    """
    Convertit Markdown en HTML (avec cache)

    Args:
        markdown_text: Texte au format Markdown

    Returns:
        HTML converti
    """
    if not markdown_text:
        return "<p>Contenu vide</p>"

    try:
        return markdown.markdown(
            markdown_text,
            extensions=[
                "extra",
                "nl2br",
                "sane_lists",
                "smarty",
                "codehilite",
                "tables",
                "fenced_code",
            ],
            output_format="html",
        )
    except Exception as e:
        logger.warning(f"⚠️  Conversion Markdown: {e}")
        paragraphs = markdown_text.split("\n\n")
        return "".join(
            f"<p>{p.replace('\n', '<br>')}</p>" for p in paragraphs if p.strip()
        )


def clean_html(html: str) -> str:
    """
    Nettoie le HTML

    Args:
        html: HTML brut

    Returns:
        HTML nettoyé
    """
    if not html:
        return "<p>Contenu non disponible</p>"

    # Supprime les caractères NULL et de contrôle
    html = html.replace("\x00", "")
    html = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", html)
    # html = sanitize_html(html)
    return html


def is_content_complete(content: str, min_length: int = 500) -> bool:
    """
    Vérifie si le contenu semble complet

    Args:
        content: Contenu HTML
        min_length: Longueur minimale requise

    Returns:
        True si le contenu est complet
    """
    if not content:
        return False

    # Supprime les balises HTML pour compter le texte réel
    text = re.sub(r"<[^>]+>", "", content).strip()

    return len(text) >= min_length


def make_absolute_url(url: str, base_url: str) -> str:
    """
    Convertit une URL relative en URL absolue

    Args:
        url: URL (relative ou absolue)
        base_url: URL de base

    Returns:
        URL absolue
    """
    if not url:
        return ""
    return urljoin(base_url, url)


def clean_tag(tag: str) -> Optional[str]:
    """
    Nettoie un tag

    Args:
        tag: Tag brut

    Returns:
        Tag nettoyé ou None si invalide
    """
    if not tag:
        return None

    # Nettoyer
    tag = tag.strip()

    # Filtrer
    if len(tag) < 3 or len(tag) > 50:
        return None

    # Supprimer les caractères spéciaux excessifs
    tag = re.sub(r"[^\w\s\-éèêàâùûôîç]", "", tag, flags=re.UNICODE)

    return tag.strip() if tag.strip() else None


def verify_token(token: Optional[str] = None) -> bool:
    """
    Vérifier la validité du token
    """
    if not token:
        return False
    # Ici on pourrait ajouter une validation plus stricte
    return len(token) > 20

