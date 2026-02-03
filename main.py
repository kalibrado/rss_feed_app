#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application RSS Feed Filter
"""

# On définit la variable d'environnement avant tout import
if __name__ == "__main__":
    import uvicorn
    from config import Config
    import os

    # Chemin du dossier central pour tous les pycache
    CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache/pycache")

    # Crée le dossier s'il n'existe pas
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.environ["PYTHONPYCACHEPREFIX"] = CACHE_DIR

    uvicorn.run(
        "app:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.APP_ENV != 'prod',
        log_level=Config.LOG_LEVEL.lower(),
        loop="asyncio",
    )
