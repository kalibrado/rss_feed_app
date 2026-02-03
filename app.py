"""
Application FastAPI - RSS Feed Filter v3.2
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from config import Config
from web.router import register_routes
from api.routes import register_api_routes

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============================================================================
# FASTAPI
# ============================================================================

app = FastAPI(
    title="RSS Feed Filter",
    version="3.2",
    description="Filtre RSS enrichi : contenu + images + tags",
)

# Middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_api_routes(app, logger)
register_routes(app, logger)

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 80)
    logger.info("🚀 RSS FEED FILTER v3.2")
    logger.info("=" * 80)
    logger.info(f"🌐 HOST: {Config.HOST}")
    logger.info(f"🔌 PORT: {Config.PORT}")
    logger.info(f"📝 LOG LEVEL: {Config.LOG_LEVEL}")
    logger.info("=" * 80)

    uvicorn.run(
        app, host=Config.HOST, port=Config.PORT, log_level=Config.LOG_LEVEL.lower()
    )
