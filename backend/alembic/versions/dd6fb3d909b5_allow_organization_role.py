"""allow organization role

Adds `organization` to the users.role CHECK constraint.

WHY THIS MIGRATION IS HAND-WRITTEN
----------------------------------
`alembic revision --autogenerate` produced an EMPTY migration for this
change. Alembic does not diff CHECK constraints -- it compares tables,
columns, indexes and foreign keys, but a changed CHECK is invisible to it.

So the Python constant and the database constraint had silently diverged:
USER_ROLES listed five roles while the database still rejected the fifth.
Nothing failed until a user actually picked "Organization" in the sign-up
form and got a 500 from a constraint violation.

**Any future change to a CHECK constraint needs a hand-written migration.**
Autogenerate will report "no changes detected" and be wrong.

WHY batch_alter_table
---------------------
SQLite cannot ALTER or DROP a constraint. Batch mode rebuilds the table:
creates a new one with the new constraint, copies the rows, drops the old,
renames. `render_as_batch` is already enabled in env.py for SQLite, but the
rebuild has to be requested explicitly here.

Revision ID: dd6fb3d909b5
Revises: 3b3e1cf60111
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "dd6fb3d909b5"
down_revision: Union[str, Sequence[str], None] = "3b3e1cf60111"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CONSTRAINT = "ck_users_role_valid"

OLD_ROLES = ("student", "developer", "researcher", "admin")
NEW_ROLES = ("student", "developer", "researcher", "organization", "admin")


def _condition(roles: Sequence[str]) -> str:
    return "role IN ('" + "', '".join(roles) + "')"


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch:
        batch.drop_constraint(CONSTRAINT, type_="check")
        batch.create_check_constraint(CONSTRAINT, _condition(NEW_ROLES))


def downgrade() -> None:
    # Any existing `organization` users would violate the narrower
    # constraint, so move them to the default role first. Losing that
    # distinction is the cost of going backwards; failing the migration
    # halfway would be worse.
    op.execute(
        sa.text("UPDATE users SET role = 'student' WHERE role = 'organization'")
    )

    with op.batch_alter_table("users", schema=None) as batch:
        batch.drop_constraint(CONSTRAINT, type_="check")
        batch.create_check_constraint(CONSTRAINT, _condition(OLD_ROLES))
