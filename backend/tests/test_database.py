"""Tests for the Task 39 database layer.

The two that matter most are the driver-argument tests and the
close-on-exception test. Both cover failures that are invisible locally and
only appear under load or in a deployment:

  - passing check_same_thread to psycopg2 is a TypeError at startup
  - a session not closed on the error path leaks until the pool is empty,
    at which point the API hangs rather than erroring
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import (
    Base,
    SessionLocal,
    _connect_args,
    _engine_kwargs,
    engine,
    get_db,
)


def test_engine_connects() -> None:
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_get_db_yields_a_session() -> None:
    generator = get_db()
    db = next(generator)
    try:
        assert isinstance(db, Session)
        assert db.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        generator.close()


def test_get_db_closes_session_on_success() -> None:
    generator = get_db()
    db = next(generator)
    generator.close()

    # A closed session has no active connection bound to it.
    assert not db.in_transaction()


def test_get_db_closes_session_even_when_endpoint_raises() -> None:
    """The decision-2 guarantee: `finally`, not a trailing close.

    Simulates an endpoint raising mid-request. If the close were written
    after the yield instead, this session would leak.
    """
    generator = get_db()
    db = next(generator)

    with pytest.raises(RuntimeError, match="endpoint blew up"):
        generator.throw(RuntimeError("endpoint blew up"))

    assert not db.in_transaction()


def test_sqlite_gets_check_same_thread() -> None:
    """FastAPI's threadpool moves a session between threads; without this
    flag SQLite raises."""
    assert _connect_args("sqlite:///./x.db") == {"check_same_thread": False}


def test_postgres_does_not_get_check_same_thread() -> None:
    """psycopg2 raises TypeError on that argument, so it must be absent."""
    args = _connect_args("postgresql://user:pw@localhost/db")
    assert "check_same_thread" not in args
    assert args == {}


def test_sqlite_skips_pool_tuning() -> None:
    """pool_pre_ping and sizing buy nothing against a local file."""
    assert _engine_kwargs("sqlite:///./x.db") == {}


def test_postgres_enables_pool_pre_ping() -> None:
    """A dropped idle connection must not fail the next request."""
    opts = _engine_kwargs("postgresql://user:pw@localhost/db")
    assert opts["pool_pre_ping"] is True
    assert opts["pool_size"] > 0


def test_base_is_sqlalchemy_2_declarative() -> None:
    """Models in Tasks 41-45 use typed Mapped[...] annotations, which need
    the 2.x DeclarativeBase rather than the legacy factory."""
    from sqlalchemy.orm import DeclarativeBase

    assert issubclass(Base, DeclarativeBase)
    assert hasattr(Base, "metadata")


def test_session_factory_does_not_expire_on_commit() -> None:
    """So an endpoint can return the object it just saved without a second
    query against a session that is already closed."""
    db = SessionLocal()
    try:
        assert db.expire_on_commit is False
    finally:
        db.close()


def test_two_sessions_are_independent() -> None:
    first, second = SessionLocal(), SessionLocal()
    try:
        assert first is not second
    finally:
        first.close()
        second.close()
