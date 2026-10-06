"""FastAPI application factory."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config, db, scheduler, security
from .routes import accounts, media, session

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


def create_app() -> FastAPI:
    db.init()

    # Bootstrap an initial UI password from the environment on first run.
    if config.INITIAL_UI_PASSWORD and not security.has_password():
        security.set_password(config.INITIAL_UI_PASSWORD)

    app = FastAPI(title=config.APP_NAME, version=config.VERSION, docs_url=None, redoc_url=None)
    app.include_router(session.router)
    app.include_router(accounts.router)
    app.include_router(media.router)

    @app.on_event("startup")
    def _start() -> None:
        scheduler.start()

    # SPA + static assets (mounted last so /api/* wins).
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


app = create_app()
