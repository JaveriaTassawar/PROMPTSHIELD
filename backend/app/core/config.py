"""Application settings, read from the environment.

Task 38. Config lives here rather than scattered through modules so Task 39
(database), Task 47 (JWT) and Task 56 (the classifier call) all read the same
values, and so nothing has to be edited between local SQLite and a deployed
Postgres.

TWO RULES THAT MATTER MORE THAN THEY LOOK:

1. NO SECRET HAS A USABLE DEFAULT.

   JWT_SECRET_KEY deliberately defaults to a placeholder that is rejected at
   startup when ENVIRONMENT is not "development". A real default would ship a
   signing key in the repo, and every token the deployed app issued could be
   forged by anyone who read the source. Failing loudly on boot is the whole
   point.

2. THE .env FILE IS NEVER COMMITTED.

   `.env.example` at the repo root lists the names; the real values stay
   local. Task 50 onward handle password hashes and tokens, so this matters
   from the first endpoint, not from deployment.
"""

from __future__ import annotations

import os
from functools import lru_cache

# What .env.example ships as the JWT placeholder. Treated as "unset".
PLACEHOLDER_SECRET = "replace-with-a-long-random-string"

# Below this, HS256 signing is weak enough to be worth refusing.
MIN_SECRET_LENGTH = 32


def _load_dotenv() -> None:
    """Read the repo-root .env into os.environ if python-dotenv is present.

    Optional on purpose: in a container the variables are already in the
    environment and there is no file to read. A missing .env is not an error.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", "..", ".."))
    load_dotenv(os.path.join(repo_root, ".env"))


class Settings:
    """Resolved configuration for one process."""

    def __init__(self) -> None:
        _load_dotenv()

        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        self.debug = self.environment == "development"

        # SQLite by default so a fresh clone runs with no database to install.
        self.database_url = os.getenv(
            "DATABASE_URL", "sqlite:///./promptshield.db"
        )

        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", PLACEHOLDER_SECRET)
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

        # Task 56 reads this. The ML inference wrapper looks for
        # PROMPTSHIELD_MODEL_PATH, so accept either name rather than making
        # the two tracks disagree about one path.
        self.model_path = (
            os.getenv("PROMPTSHIELD_MODEL_PATH")
            or os.getenv("MODEL_PATH")
            or ""
        )
        self.subtype_model_path = os.getenv(
            "PROMPTSHIELD_SUBTYPE_MODEL_PATH", ""
        )

        # Frontend dev server origins for CORS (Task 38 wires these in).
        raw_origins = os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
        )
        self.cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

        self._validate()

    def _validate(self) -> None:
        """Refuse to start with an unsafe production config.

        Checked at import rather than at first request: a server that boots
        and then issues forgeable tokens is worse than one that never boots.
        """
        if self.environment == "development":
            return

        problems = []
        if self.jwt_secret_key == PLACEHOLDER_SECRET:
            problems.append(
                "JWT_SECRET_KEY is still the .env.example placeholder"
            )
        elif len(self.jwt_secret_key) < MIN_SECRET_LENGTH:
            problems.append(
                f"JWT_SECRET_KEY is shorter than {MIN_SECRET_LENGTH} characters"
            )

        if problems:
            raise RuntimeError(
                "Unsafe configuration for ENVIRONMENT="
                f"{self.environment!r}: " + "; ".join(problems)
            )

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def __repr__(self) -> str:
        # Never render the secret, even in a traceback.
        return (
            f"Settings(environment={self.environment!r}, "
            f"database={'sqlite' if self.is_sqlite else 'postgres'}, "
            f"jwt_secret={'set' if self.jwt_secret_key != PLACEHOLDER_SECRET else 'PLACEHOLDER'})"
        )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor. FastAPI dependencies and modules both use this."""
    return Settings()
