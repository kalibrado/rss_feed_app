"""API routes ."""

import json
import secrets
import json
from fastapi import FastAPI, Query, Response, HTTPException
from fastapi.responses import RedirectResponse
from typing import Optional
import time
import requests
import feedparser
from feedgen.feed import FeedGenerator
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import Config
from api.core.cache import get_cached_feed, save_cached_feed, CACHE_TTL
from api.core.processor import process_entry
from api.core.utils import ensure_utc
from datetime import datetime

def register_api_routes(app: FastAPI, logger):

    @app.post("/api/login")
    def api_login(body: dict):
        """
        Endpoint de login avec authentification
        """
        formData = body.get("formData", {})
        username = formData.get("username")
        password = formData.get("password")

        if not username or not password:
            raise HTTPException(400, "Username et password requis")

        # Charger les utilisateurs depuis users.json
        try:
            with open("data/users.json", "r") as f:
                users = json.load(f)
        except FileNotFoundError:
            raise HTTPException(500, "Base utilisateurs non disponible")

        # Vérifier l'utilisateur
        user = next((u for u in users if u["username"] == username), None)
        if not user or user["password"] != password:
            raise HTTPException(401, "Identifiants invalides")

        # Générer un token sécurisé
        token = secrets.token_urlsafe(32)

        # Créer la réponse avec cookie sécurisé
        response = Response(
            content=json.dumps({"success": True, "token": token}),
            media_type="application/json",
        )
        response.set_cookie(
            key="session_token",
            value=token,
            max_age=3600,
            secure=True,
            httponly=True,
            samesite="strict",
        )

        return RedirectResponse(url="/?token=" + token, status_code=303)

    @app.post("/api/register")
    def api_register(credentials: dict):
        """
        Endpoint d'enregistrement nouvel utilisateur
        """

        username = credentials.get("username")
        password = credentials.get("password")

        if not username or not password or len(password) < 6:
            raise HTTPException(400, "Username et password (min 6 chars) requis")

        # Charger les utilisateurs
        try:
            with open("users.json", "r") as f:
                users = json.load(f)
        except FileNotFoundError:
            users = []

        # Vérifier si l'utilisateur existe
        if any(u["username"] == username for u in users):
            raise HTTPException(400, "Username déjà utilisé")

        # Ajouter le nouvel utilisateur
        users.append({"username": username, "password": password})

        with open("users.json", "w") as f:
            json.dump(users, f)

        return {"success": True, "message": "Utilisateur créé"}

    @app.post("/api/logout")
    def api_logout():
        """
        Endpoint de logout
        """
        response = Response(content='{"success": true}', media_type="application/json")
        response.delete_cookie("session_token")
        return response

    @app.get("/api/health")
    def health():
        """Endpoint de santé"""
        return {
            "status": "healthy",
            "version": "3.2",
            "timestamp": datetime.now().isoformat(),
            "features": {
                "full_content": True,
                "images": True,
                "tags": True,
                "enclosure": True,
            },
            "config": {
                "max_workers": Config.MAX_WORKERS,
                "jina": Config.USE_JINA,
                "cloudscraper": Config.USE_CLOUDSCRAPER,
                "playwright": Config.USE_PLAYWRIGHT,
            },
        }

    @app.get("/api/config")
    def get_config():
        """Retourne la configuration"""
        return {
            "version": "3.2",
            "workers": {
                "max": Config.MAX_WORKERS,
                "min": 1,
                "max_limit": 20,
            },
            "timeouts": {
                "request": Config.REQUEST_TIMEOUT,
                "jina": Config.JINA_TIMEOUT,
            },
            "limits": {
                "max_feed_entries": Config.MAX_FEED_ENTRIES,
                "min_content_length": Config.MIN_CONTENT_LENGTH,
                "max_tags": Config.MAX_TAGS_PER_ARTICLE,
            },
        }

    @app.get("/api/filter", response_class=Response)
    def filter(
        url: str = Query(..., description="URL du flux RSS"),
        method_extraction: Optional[str] = Query(
            None,
            description="Méthode d'extraction préférée (cascade, rss_summary, unavailable)",
        ),
        max_entries: Optional[int] = Query(
            None,
            ge=1,
            le=Config.MAX_FEED_ENTRIES,
            description="Nombre maximum d'entrées",
        ),
        workers: int = Query(
            Config.MAX_WORKERS, ge=1, le=20, description="Nombre de workers parallèles"
        ),
    ):
        """
        Filtre et enrichit un flux RSS

        Retourne un flux RSS avec:
        - Contenu complet des articles
        - Images principales (enclosure)
        - Tags/catégories
        - Dates de publication
        """
        logger.info("=" * 80)
        logger.info(f"🚀 RSS FEED FILTER v3.2")
        logger.info(f"   URL: {url}")
        logger.info(f"   Max: {max_entries or 'Toutes'} | Workers: {workers}")
        logger.info(
            f"   Extraction préférée: {method_extraction or 'Aucune, utilisation de la cascade'}"
        )
        logger.info("=" * 80)

        start_time = time.time()
        logger.info("🏁 Démarrage du traitement...")
        # ========================================================================
        # CACHE (1 heure)
        # ========================================================================

        cached = get_cached_feed(url)
        if cached:
            logger.info(f"🧠 Cache HIT (moins de {CACHE_TTL})")
            return Response(content=cached, media_type="application/rss+xml")

        logger.info("♻️ Cache MISS, génération du flux…")

        # ========================================================================
        # ÉTAPE 1: Parsing du flux RSS
        # ========================================================================
        try:
            logger.info("📖 Parsing du flux RSS...")
            parse_start = time.time()

            response = requests.get(
                url, headers=Config.HEADERS, timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            parse_elapsed = time.time() - parse_start

            if feed.bozo:
                logger.warning(f"⚠️  Flux malformé: {feed.bozo_exception}")

            if not feed.entries:
                logger.error("✗ Aucune entrée trouvée")
                raise HTTPException(404, "Aucune entrée dans le flux")

            logger.info(
                f"✓ {len(feed.entries)} entrées trouvées " f"en {parse_elapsed:.2f}s"
            )
        except HTTPException:
            raise
        except requests.HTTPError as e:
            logger.error(f"✗ Erreur HTTP: {e.response.status_code}")
            raise HTTPException(
                e.response.status_code, f"Erreur HTTP {e.response.status_code}"
            )
        except Exception as e:
            logger.error(f"✗ Erreur parsing: {str(e)[:100]}")
            raise HTTPException(400, f"Erreur: {e}")

        # ========================================================================
        # ÉTAPE 2: Limitation du nombre d'entrées
        # ========================================================================

        entries = feed.entries[:max_entries] if max_entries else feed.entries
        num_entries = len(entries)
        logger.info(f"📋 Traitement de {num_entries} entrées")
        parent = feed.feed
        # ========================================================================
        # ÉTAPE 3: Création du flux de sortie
        # ========================================================================

        fg = FeedGenerator()
        fg.title(parent.get("title", "Filtered feed"))
        fg.link(href=url)
        fg.description(feed.get("description", "Flux enrichi complet"))
        fg.language(feed.get("language", "fr"))

        # ========================================================================
        # ÉTAPE 4: Traitement parallèle des entrées
        # ========================================================================

        logger.info(f"⚙️  Traitement parallèle ({workers} workers)...")
        processing_start = time.time()

        processed = []
        failed = 0
        stats = {"cascade": 0, "rss_summary": 0, "unavailable": 0}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    process_entry, e, i + 1, num_entries, method_extraction
                ): e
                for i, e in enumerate(entries)
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        processed.append(result)
                        method = result.get("method", "unknown")
                        stats[method] = stats.get(method, 0) + 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"✗ Exception: {str(e)[:100]}")

        processing_time = time.time() - processing_start

        # Statistiques
        success_count = len(processed)
        success_rate = (success_count / num_entries * 100) if num_entries > 0 else 0
        total_images = sum(
            1 for p in processed if p.get("images", {}).get("article_image")
        )
        total_tags = sum(len(p.get("tags", [])) for p in processed)

        logger.info(f"✓ Traitement terminé en {processing_time:.1f}s")
        logger.info(f"   • Succès: {success_count}/{num_entries} ({success_rate:.1f}%)")
        logger.info(f"   • Contenu complet: {stats.get('cascade', 0)}")
        logger.info(f"   • Images: {total_images}")
        logger.info(f"   • Tags: {total_tags}")
        logger.info(f"   • Échecs: {failed}")

        # ========================================================================
        # ÉTAPE 5: Tri par date
        # ========================================================================

        processed.sort(
            key=lambda x: x["pub_date"] if x["pub_date"] else datetime.min, reverse=True
        )

        # ========================================================================
        # ÉTAPE 6: Génération du flux XML
        # ========================================================================

        logger.info("📝 Génération du flux RSS...")

        for entry_data in processed:
            fe = fg.add_entry()
            fe.id(entry_data["id"])
            fe.title(entry_data["title"])
            fe.link(href=entry_data["link"])
            fe.content(entry_data["content"], type="html")

            # Date
            if entry_data["pub_date"]:
                try:
                    pub_date = entry_data["pub_date"]
                    logger.debug(f"✓ Date avant conversion: {pub_date}")
                    pub_date = ensure_utc(entry_data["pub_date"])
                    logger.debug(f"✓ Date après conversion UTC: {pub_date}")
                    fe.pubDate(pub_date)
                except Exception as e:
                    logger.debug(f"⚠️  Erreur date: {e}")

            # Image principale (enclosure pour FreshRSS)
            images = entry_data.get("images", {})
            if images.get("article_image"):
                try:
                    fe.enclosure(
                        url=images["article_image"], length="0", type="image/jpeg"
                    )
                    logger.debug(f"✓ Image: {images['article_image'][:60]}")
                except Exception as e:
                    logger.debug(f"⚠️  Erreur image: {e}")

            # Tags
            tags = entry_data.get("tags", [])
            for tag in tags:
                try:
                    fe.category(term=tag)
                except Exception as e:
                    logger.debug(f"⚠️  Erreur tag '{tag}': {e}")

        # Génération du XML
        try:
            rss = fg.rss_str(pretty=True)
        except Exception as e:
            logger.error(f"✗ Erreur génération RSS: {e}")
            raise HTTPException(500, "Erreur génération du flux")

        rss_size = len(rss)
        total_time = time.time() - start_time

        logger.info(f"✓ Flux généré ({rss_size:,} octets)")
        logger.info(f"🏁 Terminé en {total_time:.1f}s")
        logger.info("=" * 80)
        save_cached_feed(url, rss)
        return Response(content=rss, media_type="application/rss+xml")
