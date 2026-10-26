"""Database engine, session factory and the `get_db()` dependency.

Task 39. Every endpoint from Task 50 onward takes a session from `get_db()`,
and the five models in Tasks 41-45 inherit from `Base` here.

FOUR DECISIONS THAT ARE NOT OBVIOUS:

1. SQLITE NEEDS check_same_thread=False, POSTGRES MUST NOT GET IT.

   SQLite's driver refuses by default to use one connection from more than
   one thread. FastAPI runs sync endpoints in a threadpool, so a session
   opened on one thread and used on another raises
   "SQLite objects created in a thread can only be used in that same thread".
   The flag lifts that check, which is safe here because SQLAlchemy's pool
   hands each session its own connection.

   The flag is SQLite-only -- passing it to psycopg2 is a TypeError. Hence
   `_connect_args()` rather than one hardcoded dict, so the same module
   serves local SQLite and a deployed Postgres with no edit.

2. THE SESSION IS CLOSED IN A `finally`, NOT AFTER THE YIELD.

   If an endpoint raises, a `db.close()` written after the yield never runs
   and the connection leaks back to nothing. Under load that exhausts the
   pool and the API starts hanging rather than erroring -- a failure that
   looks like a network problem and is miserable to trace. `finally`
   guarantees the close on both paths.

   `get_db()` deliberately does NOT commit. Each endpoint commits its own
   unit of work, because a dependency that auto-commits would persist half a
   failed operation.

3. Base IS A 2.x DeclarativeBase, NOT declarative_base().

   SQLAlchemy 2.1 is installed. The legacy `declarative_base()` factory
   still works but is the 1.x idiom and mixes badly with the typed
   `Mapped[...]` annotations the models in Tasks 41-45 will use.

4. pool_pre_ping IS ON FOR POSTGRES.

   A pooled connection can be dropped by the server or a proxy while idle.
   Without pre-ping the next request gets a stale socket and fails once
   before the pool replaces it. Pointless for a local SQLite file, so it is
   applied only when it earns its cost.

Run:  python -m app.core.database      (self-check)
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for every model in Tasks 41-45.

    Alembic's autogenerate (Task 40) reads `Base.metadata`, so a model that
    is defined but never imported is invisible to migrations. `app/models/
    __init__.py` imports them all for exactly that reason.
    """


def _connect_args(database_url: str) -> dict:
    """Driver arguments that apply to SQLite only -- see decision 1."""
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _engine_kwargs(database_url: str) -> dict:
    """Pool settings worth paying for only on a real network database."""
    if database_url.startswith("sqlite"):
        return {}
    return {
        "pool_pre_ping": True,  # see decision 4
        "pool_size": 5,
        "max_overflow": 10,
    }


settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(settings.database_url),
    # Echo SQL only in development; it is far too noisy in a deployment and
    # would log prompt text, which is user content.
    echo=False,
    **_engine_kwargs(settings.database_url),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    # expire_on_commit=False keeps attributes readable after commit, so an
    # endpoint can return the object it just saved without a second query
    # that would fail once the session is closed.
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding one session per request.

    Usage:
        @router.post("/thing")
        def create(payload: ThingIn, db: Session = Depends(get_db)):
            ...
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # See decision 2 -- must be `finally`, not a trailing statement.
        db.close()


def _self_check() -> int:
    """Prove the engine connects and a session round-trips."""
    from sqlalchemy import text

    print(f"database : {settings.database_url}")
    print(f"dialect  : {engine.dialect.name}")
    print(f"connect_args: {_connect_args(settings.database_url)}")
    print(f"pool opts   : {_engine_kwargs(settings.database_url) or '(sqlite: none)'}")

    with engine.connect() as connection:
        value = connection.execute(text("SELECT 1")).scalar_one()
    print(f"\nSELECT 1 -> {value}")
    if value != 1:
        print("FAIL: unexpected result")
        return 1

    # Exercise the dependency the way FastAPI does, generator included.
    generator = get_db()
    session = next(generator)
    try:
        session.execute(text("SELECT 1"))
        print("get_db() yielded a working session")
    finally:
        generator.close()

    print(f"tables registered on Base.metadata: "
          f"{len(Base.metadata.tables)} "
          f"{sorted(Base.metadata.tables) or '(none yet -- Tasks 41-45)'}")
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
