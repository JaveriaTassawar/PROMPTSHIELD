"""MitigationAction model.

Task 45. What the system *did* about an attack, as opposed to Task 43 which
records what it *found*. Written by the mitigation logic in Task 57.

FOUR DECISIONS:

1. SEVERAL ACTIONS PER ANALYSIS ARE ALLOWED.

   Unlike AnalysisResult and AttackSubtype, the FK here is NOT unique. One
   prompt can legitimately be warned about and rewritten, or blocked after a
   warning. Forcing one row would make the second action overwrite the first
   and lose the audit trail -- and an audit trail is the point of this
   table.

2. mitigated_prompt IS NULLABLE, AND IS NOT THE ORIGINAL.

   Only the `rewriting` action produces one. A warning or a block has
   nothing to store. Keeping it null rather than copying the original makes
   "was this rewritten?" answerable without a string comparison.

   The original prompt stays on Prompt.prompt_text. Never overwrite that --
   the Task 60-63 analytics and any audit need what the user actually typed.

3. action_type IS CHECK-CONSTRAINED TO THE PLAN'S THREE VALUES.

   warning / blocking / rewriting, exactly as the plan names them. A typo
   would leave an action no UI branch matches, so the prompt would appear
   unhandled.

4. THE TABLE IS APPEND-ONLY BY CONVENTION.

   Nothing enforces it in SQL, but rows here are a record of what happened.
   Task 57 should insert, never update: rewriting history is exactly what an
   audit trail must not allow.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis import AnalysisResult

# Exactly the three the plan names for Task 45 and Task 57.
ACTION_TYPES = ("warning", "blocking", "rewriting")

# Only this one produces a mitigated_prompt -- see decision 2.
REWRITING = "rewriting"


class MitigationAction(Base):
    """One action taken in response to an analysis."""

    __tablename__ = "mitigation_actions"

    mitigation_id: Mapped[int] = mapped_column(primary_key=True)

    # NOT unique -- several actions per analysis are valid. See decision 1.
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_results.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_type: Mapped[str] = mapped_column(String(20), nullable=False)

    action_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Populated only for `rewriting`. Text, because a rewritten prompt is as
    # long as the original -- which the ML work measured up to ~3,900 tokens.
    mitigated_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    action_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    analysis: Mapped["AnalysisResult"] = relationship(
        "AnalysisResult", back_populates="mitigations"
    )

    __table_args__ = (
        CheckConstraint(
            "action_type IN ('" + "', '".join(ACTION_TYPES) + "')",
            name="ck_mitigation_action_type_valid",
        ),
        # A rewrite with nothing rewritten is a bug, not a state. Catching
        # it here means Task 57 cannot quietly record an empty rewrite.
        CheckConstraint(
            "action_type != 'rewriting' OR mitigated_prompt IS NOT NULL",
            name="ck_mitigation_rewrite_has_text",
        ),
        # Tasks 60-63 count actions by kind over time.
        Index("ix_mitigation_type_time", "action_type", "action_time"),
    )

    @property
    def is_rewrite(self) -> bool:
        return self.action_type == REWRITING

    def __repr__(self) -> str:
        # mitigated_prompt is user-derived content; do not render it in full.
        return (
            f"MitigationAction(mitigation_id={self.mitigation_id}, "
            f"analysis_id={self.analysis_id}, action={self.action_type!r})"
        )
