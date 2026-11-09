"""Shared test fixtures.

The `client` fixture overrides `get_db` so endpoint tests run against a
throwaway database rather than `backend/promptshield.db`. Without the
override, tests would write real rows into the development database and
their results would depend on whatever was left there by the last run.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import app.core.database  # noqa: F401  -- registers the SQLite FK pragma
from app.core.database import Base, get_db
from app.main import create_app


@pytest.fixture
def db_session(tmp_path) -> Session:
    """An isolated database for one test."""
    engine = create_engine(f"sqlite:///{tmp_path / 'api_test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """A TestClient whose endpoints use `db_session`.

    The override yields the *same* session the test holds, so a test can
    inspect rows the endpoint wrote without opening a second connection
    that would not see uncommitted state.
    """
    application = create_app()

    def _override_get_db():
        try:
            yield db_session
        finally:
            # The db_session fixture owns the lifecycle; closing here
            # would end it before the test could read anything.
            pass

    application.dependency_overrides[get_db] = _override_get_db
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
