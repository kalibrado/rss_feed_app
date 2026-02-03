import hashlib
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path("cache/flux")
CACHE_TTL = timedelta(hours=2)

CACHE_DIR.mkdir(parents=True, exist_ok=True)


def cache_key_from_url(url: str, extra: str = "") -> str:
    key = f"{url}|{extra}"
    return hashlib.sha1(key.encode()).hexdigest() + ".xml"

def get_cached_feed(url: str) -> bytes | None:
    """Retourne le flux depuis le cache s'il est valide"""
    cache_file = CACHE_DIR / cache_key_from_url(url)

    if not cache_file.exists():
        return None

    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
    if datetime.now() - mtime > CACHE_TTL:
        return None

    return cache_file.read_bytes()


def save_cached_feed(url: str, content: bytes):
    """Sauvegarde le flux dans le cache"""
    cache_file = CACHE_DIR / cache_key_from_url(url)
    cache_file.write_bytes(content)
