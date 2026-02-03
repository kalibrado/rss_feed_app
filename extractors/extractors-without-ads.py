"""
Extraction de contenu, images et tags depuis le HTML
"""
import re
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from config import Config
from rss_feed_app.api.core.utils import make_absolute_url, is_content_complete, clean_tag

logger = logging.getLogger(__name__)

# Import optionnel de BeautifulSoup
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup non disponible - extraction limitée")

"""
Extraction et nettoyage du contenu principal d'un article HTML
"""

BAD_KEYWORDS = [
    # Cookies / privacy
    "cookie", "consent", "gdpr", "privacy",

    # Pub / tracking
    "advert", "ads", "pub", "sponsor", "promo", "banner",

    # Réseaux sociaux
    "social", "share", "follow",

    # Newsletter
    "newsletter", "subscribe",

    # Navigation / layout
    "footer", "header", "nav", "sidebar",

    # Recommandations
    "recommend", "related", "suggest",

    # Commentaires
    "comment", "comments", "commentaire", "commentaires",
    "responses", "reply", "discussion", "disqus",
    "fb-comments", "facebook-comments"
]


def clean_article_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Supprimer scripts & styles uniquement
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    # Supprimer iframes non éditoriales
    for iframe in soup.find_all("iframe", src=True):
        src = iframe["src"].lower()
        if any(x in src for x in ["disqus", "facebook", "ads", "doubleclick"]):
            iframe.decompose()

    # Supprimer blocs parasites MAIS PAS les conteneurs éditoriaux
    for tag in soup.find_all(True):
        tag_name = tag.name.lower()

        if tag_name in ["article", "section", "figure", "picture", "img"]:
            continue  # ⛔ on touche pas

        identifiers = " ".join([
            " ".join(tag.get("class", [])),
            tag.get("id", "") or ""
        ]).lower()

        if any(k in identifiers for k in BAD_KEYWORDS):
            tag.decompose()

    # Supprimer commentaires explicitement
    for tag in soup.find_all(
        ["section", "div"],
        id=re.compile(r'comment|disqus|reply', re.I)
    ):
        tag.decompose()

    return str(soup)


def extract_article_content(html: str) -> str:
    """
    Extrait le contenu principal de l'article puis le nettoie
    """
    if not html:
        return "<p>Contenu non disponible</p>"

    soup = BeautifulSoup(html, "html.parser")

    strategies = [
        ("article", None),
        ("main", None),
        ("div", lambda x: x and any(
            c in x.lower() || x for c in ["content", "article", "post", "entry", "main"]
        )),
    ]

    for tag, class_filter in strategies:
        element = soup.find(tag, class_=class_filter) if class_filter else soup.find(tag)
        if element:
            content_html = str(element)
            if is_content_complete(content_html, Config.MIN_CONTENT_LENGTH):
                logger.debug(f"✓ Contenu extrait depuis <{tag}>")
                return clean_article_html(content_html)

    # Fallback body
    body = soup.find("body")
    if body:
        logger.debug("⚠️ Fallback: extraction depuis <body>")
        return clean_article_html(str(body))

    return clean_article_html(html)

def extract_images(html: str, base_url: str) -> Dict[str, Optional[str]]:
    """
    Extrait les images depuis le HTML
    
    Args:
        html: HTML de la page
        base_url: URL de base pour les URLs relatives
        
    Returns:
        {
            "article_image": URL de l'image principale,
            "site_logo": URL du logo du site,
            "favicon": URL du favicon
        }
    """
    result = {
        "article_image": None,
        "site_logo": None,
        "favicon": None
    }
    
    if not BS4_AVAILABLE or not html:
        return result
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        base_domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        
        # IMAGE PRINCIPALE DE L'ARTICLE
        # Priorité 1: Open Graph
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            result["article_image"] = make_absolute_url(og_image['content'], base_url)
            logger.debug(f"✓ Image article (og:image)")
        
        # Priorité 2: Twitter Card
        if not result["article_image"]:
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                result["article_image"] = make_absolute_url(twitter_image['content'], base_url)
                logger.debug(f"✓ Image article (twitter:image)")
        
        # Priorité 3: Première image dans <article>
        if not result["article_image"]:
            article_tag = soup.find('article') or soup.find('main')
            if article_tag:
                img = article_tag.find('img', src=True)
                if img and img.get('src'):
                    src = img.get('src', '')
                    if not any(x in src.lower() for x in ['icon', 'logo', 'avatar', 'emoji']):
                        result["article_image"] = make_absolute_url(src, base_url)
                        logger.debug(f"✓ Image article (première img)")
        
        # LOGO DU SITE
        # Priorité 1: og:logo
        og_logo = soup.find('meta', property='og:logo')
        if og_logo and og_logo.get('content'):
            result["site_logo"] = make_absolute_url(og_logo['content'], base_url)
            logger.debug(f"✓ Logo site (og:logo)")
        
        # Priorité 2: Logo dans header
        if not result["site_logo"]:
            header = soup.find('header')
            if header:
                logo_img = header.find('img', src=True, alt=re.compile(r'logo', re.I))
                if logo_img:
                    result["site_logo"] = make_absolute_url(logo_img['src'], base_url)
                    logger.debug(f"✓ Logo site (header)")
        
        # FAVICON
        # Priorité 1: apple-touch-icon
        apple_icon = soup.find('link', rel=re.compile(r'apple-touch-icon', re.I))
        if apple_icon and apple_icon.get('href'):
            result["favicon"] = make_absolute_url(apple_icon['href'], base_url)
            logger.debug(f"✓ Favicon (apple)")
        
        # Priorité 2: icon standard
        if not result["favicon"]:
            icon = soup.find('link', rel=re.compile(r'icon', re.I))
            if icon and icon.get('href'):
                result["favicon"] = make_absolute_url(icon['href'], base_url)
                logger.debug(f"✓ Favicon (icon)")
        
        # Fallback favicon
        if not result["favicon"]:
            result["favicon"] = f"{base_domain}/favicon.ico"
        
        # Utiliser favicon comme logo si pas de logo
        if not result["site_logo"] and result["favicon"]:
            result["site_logo"] = result["favicon"]
            logger.debug("✓ Logo = Favicon (fallback)")
        
        return result
        
    except Exception as e:
        logger.warning(f"⚠️  Erreur extraction images: {e}")
        return result


def extract_tags(html: str, rss_categories: Optional[List[str]] = None) -> List[str]:
    """
    Extrait les tags/catégories depuis le HTML
    
    Args:
        html: HTML de l'article
        rss_categories: Catégories du flux RSS
        
    Returns:
        Liste de tags uniques
    """
    tags = set()
    
    # Ajouter les catégories du flux RSS
    if rss_categories:
        tags.update(rss_categories)
        logger.debug(f"✓ Tags RSS: {rss_categories}")
    
    if not BS4_AVAILABLE or not html:
        return list(tags)
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Meta keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            keywords = [k.strip() for k in keywords_meta['content'].split(',')]
            tags.update(keywords)
            logger.debug(f"✓ Tags meta keywords: {keywords[:3]}")
        
        # 2. Article:tag (Open Graph)
        article_tags = soup.find_all('meta', property='article:tag')
        if article_tags:
            for tag in article_tags:
                if tag.get('content'):
                    tags.add(tag['content'].strip())
            logger.debug(f"✓ Tags article:tag: {len(article_tags)}")
        
        # 3. Liens de catégorie
        tag_links = soup.find_all('a', class_=re.compile(r'(tag|category|label|topic)', re.I))
        if tag_links:
            for link in tag_links[:10]:
                text = link.get_text(strip=True)
                if text and len(text) < 30:
                    tags.add(text)
            logger.debug(f"✓ Tags depuis liens: {len(tag_links)}")
        
        # Nettoyer les tags
        cleaned_tags = []
        for tag in tags:
            cleaned = clean_tag(tag)
            if cleaned:
                cleaned_tags.append(cleaned)
        
        # Limiter et trier
        cleaned_tags = sorted(set(cleaned_tags))[:Config.MAX_TAGS_PER_ARTICLE]
        
        logger.debug(f"✓ Tags finaux: {cleaned_tags}")
        return cleaned_tags
        
    except Exception as e:
        logger.warning(f"⚠️  Erreur extraction tags: {e}")
        return list(tags) if tags else []