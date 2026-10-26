"""Alembic environment.

Task 40. Rewritten from the generated template so migrations and the running
app can never disagree about two things: which database they point at, and
what the schema is supposed to look like.

THREE DECISIONS THAT MATTER:

1. THE URL COMES FROM app.core.config, NOT FROM alembic.ini.

   The generated template hardcodes `sqlalchemy.url` in alembic.ini. Leaving
   it there means a deployment with DATABASE_URL set to Postgres would still
   run migrations against the local SQLite file -- the app and its schema
   would silently point at different databases. Reading get_settings() makes
   one value authoritative, and keeps credentials out of a committed file.

2. target_metadata IS Base.metadata, WITH EVERY MODEL IMPORTED.

   Autogenerate diffs the database against Base.metadata. A model class that
   is never imported does not register on that metadata, so autogenerate
   emits an empty migration and the table is quietly missing. Importing
   `app.models` pulls in all of them -- which is why that package's
   __init__.py must re-export every model as Tasks 41-45 add them.

3. render_as_batch IS ON FOR SQLITE.

   SQLite cannot ALTER a column. Without batch mode, the first migration that
   changes or drops one fails outright. Batch mode makes Alembic rebuild the
   table instead. Harmless on Postgres, essential locally.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Make `app` importable when alembic runs from the backend/ directory.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base  # noqa: E402

# Registers every model on Base.metadata -- see decision 2. Tasks 41-45 add
# to app/models/__init__.py; nothing here needs to change as they land.
import app.models  # noqa: E402,F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()

# Decision 1: the app's URL wins over anything in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata

# Decision 3: SQLite cannot ALTER columns.
RENDER_AS_BATCH = settings.is_sqlite


def run_migrations_offline() -> None:
    """Emit SQL to stdout without connecting (`alembic upgrade --sql`)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=RENDER_AS_BATCH,
        # Without this, a column whose type changes is not detected.
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and apply migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=RENDER_AS_BATCH,
            compare_type=True,
            # Detects a server-default that changed, which autogenerate
            # otherwise ignores.
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
