"""Tests for the Task 41 User model.

Each test here covers a way bad data could reach the database. They run
against a real SQLite file rather than a mock, because the things being
tested -- UNIQUE, CHECK, server defaults -- are enforced by the database,
not by Python, and a mock would pass while the real schema let the row in.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.user import (
    BCRYPT_HASH_LENGTH,
    DEFAULT_ROLE,
    USER_ROLES,
    User,
    normalise_email,
)

# A real bcrypt hash is 60 chars; shape matters for the column width.
FAKE_HASH = "$2b$12$" + "x" * 53


@pytest.fixture
def db(tmp_path) -> Session:
    """A throwaway database per test, with CHECK constraints enforced.

    SQLite ignores foreign keys unless asked, and a file database is used
    rather than :memory: so the schema matches what Alembic produces.
    """
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def make_user(**overrides) -> User:
    values = {
        "user_name": "Jawaria",
        "email": "jawaria@ucp.edu.pk",
        "password_hash": FAKE_HASH,
    }
    values.update(overrides)
    return User(**values)


def test_user_persists_with_defaults(db: Session) -> None:
    db.add(make_user())
    db.commit()

    user = db.query(User).one()
    assert user.user_id is not None
    assert user.role == DEFAULT_ROLE
    assert user.is_active is True
    assert user.created_at is not None, "server_default should populate this"


def test_email_must_be_unique(db: Session) -> None:
    db.add(make_user())
    db.commit()

    db.add(make_user(user_name="Someone Else"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_email_is_required(db: Session) -> None:
    db.add(make_user(email=None))
    with pytest.raises(IntegrityError):
        db.commit()


def test_password_hash_is_required(db: Session) -> None:
    """A user row with no credential must not be storable."""
    db.add(make_user(password_hash=None))
    with pytest.raises(IntegrityError):
        db.commit()


@pytest.mark.parametrize("role", USER_ROLES)
def test_every_declared_role_is_accepted(db: Session, role: str) -> None:
    db.add(make_user(email=f"{role}@ucp.edu.pk", role=role))
    db.commit()
    assert db.query(User).one().role == role


def test_invalid_role_is_rejected_by_the_database(db: Session) -> None:
    """A typo like 'admim' would silently remove access in Task 55, with
    no error anywhere, so the database refuses it."""
    db.add(make_user(role="admim"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_normalise_email_lowercases_and_strips() -> None:
    assert normalise_email("  Jawaria@UCP.edu.PK ") == "jawaria@ucp.edu.pk"


def test_normalisation_prevents_duplicate_accounts(db: Session) -> None:
    """Without normalising, these two are different rows under a UNIQUE
    index -- a duplicate-registration hole, and a login that only works
    with the original casing."""
    db.add(make_user(email=normalise_email("Jawaria@UCP.edu.pk")))
    db.commit()

    db.add(make_user(email=normalise_email("jawaria@ucp.edu.pk")))
    with pytest.raises(IntegrityError):
        db.commit()


def test_column_is_named_password_hash_not_password() -> None:
    """Naming it `password` invites storing plaintext at the call site.

    This project is about security; a plaintext password column would
    undercut it.
    """
    columns = User.__table__.columns.keys()
    assert "password_hash" in columns
    assert "password" not in columns


def test_password_column_fits_a_bcrypt_hash() -> None:
    assert User.__table__.c.password_hash.type.length == BCRYPT_HASH_LENGTH


def test_repr_never_leaks_the_hash(db: Session) -> None:
    """repr() lands in logs and tracebacks."""
    user = make_user()
    db.add(user)
    db.commit()

    assert FAKE_HASH not in repr(user)
    assert "jawaria@ucp.edu.pk" in repr(user)


def test_model_is_registered_for_autogenerate() -> None:
    """If this fails, Alembic emits an empty migration and the table is
    silently missing -- see app/models/__init__.py."""
    import app.models

    assert "users" in Base.metadata.tables
    assert hasattr(app.models, "User")
