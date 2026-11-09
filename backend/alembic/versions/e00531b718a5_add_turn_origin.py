"""add turn origin

Revision ID: e00531b718a5
Revises: 30eb1408b4d1
Create Date: 2026-11-09 23:37:04.800543

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e00531b718a5'
down_revision: Union[str, Sequence[str], None] = '30eb1408b4d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add `origin` and its CHECK constraint.

    Autogenerate produced only the add_column. It does not diff CHECK
    constraints -- the same gotcha as migration dd6fb3d909b5 -- so the
    constraint here is hand-written. Without it the Python constant would
    permit values the database does not, and they would diverge silently.
    """
    with op.batch_alter_table("scenario_turns", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "origin",
                sa.String(length=20),
                nullable=False,
                # Required: existing rows need a value for a NOT NULL
                # column. 'authored' is the safer default -- claiming
                # written text is dataset-sourced would overstate the
                # evidence behind a scenario.
                server_default="authored",
            )
        )
        batch_op.create_check_constraint(
            "ck_turn_origin_valid", "origin IN ('dataset', 'authored')"
        )


def downgrade() -> None:
    """Drop the constraint before the column it constrains."""
    with op.batch_alter_table("scenario_turns", schema=None) as batch_op:
        batch_op.drop_constraint("ck_turn_origin_valid", type_="check")
        batch_op.drop_column("origin")
