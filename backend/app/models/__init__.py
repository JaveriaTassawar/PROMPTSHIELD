"""SQLAlchemy models.

EVERY MODEL MUST BE IMPORTED HERE.

Alembic's autogenerate diffs the live database against `Base.metadata`, and a
model class only registers on that metadata when its module is imported.
A model that exists on disk but is missing from this file produces an *empty*
migration -- Alembic reports "no changes detected", the table is silently
absent from the schema, and the first query against it fails at runtime with
"no such table".

`alembic/env.py` imports this package for exactly that reason. Add each model
below as Tasks 41-45 land:

    Task 41  User
    Task 42  Prompt
    Task 43  AnalysisResult
    Task 44  AttackSubtype
    Task 45  MitigationAction
"""

from __future__ import annotations

# Re-exported so `import app.models` registers everything on Base.metadata.
from app.models.prompt import Prompt  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ["Prompt", "User"]
