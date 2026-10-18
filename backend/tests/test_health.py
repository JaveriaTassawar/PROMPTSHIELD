"""Tests for the Task 38 scaffold.

Covers the three things the scaffold promises: the app builds, /health
answers, and the config refuses to run unsafely in production.

That last test is the one worth having. It is easy to write a config module
that validates nothing and only discover it when a deployed instance signs
tokens with a key from the public repo.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import PLACEHOLDER_SECRET, Settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "promptshield-api"


def test_health_reports_config_state(client: TestClient) -> None:
    """The point of /health is diagnosing a new machine, so these keys
    must be present even when nothing is configured."""
    body = client.get("/health").json()

    for key in ("environment", "database", "model_configured",
                "subtype_model_configured"):
        assert key in body, f"/health is missing {key!r}"

    assert isinstance(body["model_configured"], bool)


def test_root_points_at_docs(client: TestClient) -> None:
    body = client.get("/").json()
    assert body["docs"] == "/docs"
    assert body["health"] == "/health"


def test_openapi_schema_builds(client: TestClient) -> None:
    """A broken response model shows up here rather than at /docs."""
    schema = client.get("/openapi.json")
    assert schema.status_code == 200
    assert "/health" in schema.json()["paths"]


def test_placeholder_secret_rejected_outside_development(monkeypatch) -> None:
    """Production must not boot with the .env.example placeholder."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", PLACEHOLDER_SECRET)

    with pytest.raises(RuntimeError, match="placeholder"):
        Settings()


def test_short_secret_rejected_outside_development(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "too-short")

    with pytest.raises(RuntimeError, match="shorter than"):
        Settings()


def test_long_secret_accepted_in_production(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 48)

    settings = Settings()
    assert settings.environment == "production"
    assert settings.debug is False


def test_development_allows_placeholder(monkeypatch) -> None:
    """Local work must not require generating a key first."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", PLACEHOLDER_SECRET)

    settings = Settings()
    assert settings.debug is True


def test_repr_never_leaks_the_secret(monkeypatch) -> None:
    """A traceback or log line must not print the signing key."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("JWT_SECRET_KEY", "super-secret-value-that-must-not-leak")

    assert "super-secret" not in repr(Settings())


def test_model_path_accepts_either_env_name(monkeypatch) -> None:
    """The ML wrapper uses PROMPTSHIELD_MODEL_PATH; .env.example used
    MODEL_PATH. Both resolve, so the two tracks cannot disagree."""
    monkeypatch.delenv("PROMPTSHIELD_MODEL_PATH", raising=False)
    monkeypatch.setenv("MODEL_PATH", "/some/checkpoint")
    assert Settings().model_path == "/some/checkpoint"

    monkeypatch.setenv("PROMPTSHIELD_MODEL_PATH", "/preferred/checkpoint")
    assert Settings().model_path == "/preferred/checkpoint"
