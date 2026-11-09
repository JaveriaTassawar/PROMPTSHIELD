"""Health endpoint.

Task 38. `GET /health` is what the frontend dev server, a deploy check and
Task 66's smoke test all hit to answer one question: is the API up?

It deliberately reports *more* than "ok" — whether a model path is
configured, and which database backend is in use. Those are the two things
most likely to be misconfigured on a new machine, and finding out here beats
discovering it when Task 56 returns a 500.

It does NOT touch the database or load the model. A health check that depends
on the slowest part of the system fails for reasons unrelated to health, and
loading a 268 MB checkpoint per probe would make it useless.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.services import classifier as classifier_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness check. No database query, no model load."""
    settings = get_settings()

    return {
        "status": "ok",
        "service": "promptshield-api",
        "environment": settings.environment,
        "database": "sqlite" if settings.is_sqlite else "postgresql",
        # Reported so a misconfigured deployment is visible before the first
        # /api/analyze-prompt call rather than after it.
        "model_configured": bool(settings.model_path),
        # Actually importable and loadable, not merely configured --
        # a path pointing at nothing would otherwise look healthy.
        "model_available": classifier_service.is_available(),
        "subtype_model_configured": bool(settings.subtype_model_path),
    }
