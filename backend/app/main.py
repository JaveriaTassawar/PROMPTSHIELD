"""PromptShield API entry point.

Task 38. The app is built by a factory rather than created at module level so
tests can construct an isolated instance, and so importing this module does
not start wiring things up as a side effect.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs

CORS IS CONFIGURED FROM SETTINGS, NOT WILDCARDED.

`allow_origins=["*"]` together with `allow_credentials=True` is rejected by
browsers, and it would also let any site call this API with a logged-in
user's cookies once Task 47 adds JWT auth. The origin list comes from
CORS_ORIGINS and defaults to the Vite and CRA dev-server ports, which is what
Rana's frontend (Task 67 onward) runs on.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import analysis, auth, health

API_TITLE = "PromptShield API"
API_VERSION = "0.1.0"
API_DESCRIPTION = (
    "Detects, classifies and mitigates prompt injection attacks. "
    "Classification is 3-class — Safe, Direct Jailbreak, Indirect Injection — "
    "with an optional attack sub-type."
)


def create_app() -> FastAPI:
    """Build and configure the application."""
    settings = get_settings()

    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers go INSIDE the factory. A route registered after create_app()
    # returns attaches only to the module-level instance and 404s in any
    # app a test builds -- see the Task 38 note below.
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(analysis.router)

    # Registered inside the factory, not on the module-level `app` below.
    # A decorator applied after create_app() returns would attach only to
    # that one instance, so any app built by a test would 404 here -- which
    # is exactly what test_root_points_at_docs caught.
    @app.get("/", tags=["root"])
    def root() -> dict:
        """Points a curious visitor at the docs instead of returning 404."""
        return {
            "service": "promptshield-api",
            "version": API_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
