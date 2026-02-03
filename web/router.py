"""Routes pour l'interface web."""

from typing import Optional
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="web/templates")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

def register_routes(app: FastAPI, logger):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    @app.get("/")
    def root(token: Optional[str] = Query(None)):
        if not token:
            return RedirectResponse(url="/login", status_code=303)
        context = {"request": {}, "token": token}
        return templates.TemplateResponse("index.html", context)

    @app.get("/login")
    def login():
        return templates.TemplateResponse("pages/login.html", {"request": {}})

    @app.get("/register")
    def register():
        return templates.TemplateResponse("pages/register.html", {"request": {}})
