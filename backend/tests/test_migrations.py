"""Tests for the Task 40 Alembic setup.

The valuable test here is `test_env_py_overrides_ini_url`. The generated
template hardcodes a URL in alembic.ini, and leaving it would let a
deployment run migrations against the wrong database while the app used
DATABASE_URL -- app and schema silently diverging, with nothing failing.

`test_models_package_is_imported_by_env` guards the other silent failure:
autogenerate diffs against Base.metadata, so a model missing from
app/models/__init__.py yields an empty migration and a missing table that
only surfaces as "no such table" at runtime.
"""

from __future__ import annotations

import configparser
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
ENV_PY = BACKEND_ROOT / "alembic" / "env.py"
VERSIONS = BACKEND_ROOT / "alembic" / "versions"


def test_alembic_ini_has_no_hardcoded_url() -> None:
    """A real URL here would override DATABASE_URL in a deployment and
    commit credentials to the repo."""
    parser = configparser.ConfigParser()
    parser.read(ALEMBIC_INI)

    url = parser.get("alembic", "sqlalchemy.url", fallback="").strip()
    assert url == "", (
        f"alembic.ini pins sqlalchemy.url to {url!r}. It must stay blank so "
        "env.py can supply settings.database_url."
    )


def test_env_py_overrides_ini_url() -> None:
    """env.py must set the URL from app settings at runtime."""
    source = ENV_PY.read_text(encoding="utf-8")

    assert "set_main_option" in source
    assert "settings.database_url" in source
    assert "get_settings" in source


def test_env_py_targets_base_metadata() -> None:
    source = ENV_PY.read_text(encoding="utf-8")
    assert "target_metadata = Base.metadata" in source


def test_models_package_is_imported_by_env() -> None:
    """Without this import, autogenerate cannot see any model and silently
    produces empty migrations."""
    source = ENV_PY.read_text(encoding="utf-8")
    assert "import app.models" in source


def test_batch_mode_enabled_for_sqlite() -> None:
    """SQLite cannot ALTER a column; without batch mode the first migration
    that changes one fails outright."""
    source = ENV_PY.read_text(encoding="utf-8")
    assert "render_as_batch" in source
    assert "settings.is_sqlite" in source


def test_type_comparison_enabled() -> None:
    """Off by default, which means a changed column type is not detected."""
    source = ENV_PY.read_text(encoding="utf-8")
    assert "compare_type=True" in source


def test_a_migration_exists() -> None:
    revisions = [p for p in VERSIONS.glob("*.py") if p.name != "__init__.py"]
    assert revisions, "no migration in alembic/versions"


def test_every_migration_has_upgrade_and_downgrade() -> None:
    """A migration without a working downgrade cannot be rolled back, which
    matters the first time one is wrong in a deployment."""
    for revision in VERSIONS.glob("*.py"):
        if revision.name == "__init__.py":
            continue
        source = revision.read_text(encoding="utf-8")
        assert "def upgrade()" in source, f"{revision.name} has no upgrade()"
        assert "def downgrade()" in source, f"{revision.name} has no downgrade()"


def test_models_init_documents_the_import_requirement() -> None:
    """The next person adding a model needs to know why this file matters."""
    source = (BACKEND_ROOT / "app" / "models" / "__init__.py").read_text(
        encoding="utf-8"
    )
    assert "autogenerate" in source.lower()
