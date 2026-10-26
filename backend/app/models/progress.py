"""LearningProgress model.

Task 49. Tracks a user through the Learning Hub modules -- the taught
content, as distinct from Task 48's practice sessions.

THREE DECISIONS:

1. (user_id, module_name) IS UNIQUE.

   A user has one progress record per module, which they move through
   rather than accumulating. Without the constraint, re-opening a module
   appends a second row and every completion count is inflated -- the kind
   of error that makes a progress bar read 150%.

   This is the first composite unique constraint in the schema; the others
   were single columns.

2. comp_status IS CHECK-CONSTRAINED, WITH `not_started` AS THE DEFAULT.

   Storing `not_started` explicitly, rather than leaving the row absent,
   means "has this user ever opened this module?" and "have they finished
   it?" are different queries. A missing row would conflate them.

3. completed_at IS NULL UNLESS comp_status IS `completed`.

   Enforced by CHECK, both directions: a completed module must have a
   timestamp, and an unfinished one must not. Without it, a module could
   read `in_progress` while carrying a completion date -- which the Task 63
   analytics would count as finished.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User

COMPLETION_STATUSES = ("not_started", "in_progress", "completed")
DEFAULT_STATUS = "not_started"
COMPLETED = "completed"


class LearningProgress(Base):
    """One user's progress through one Learning Hub module."""

    __tablename__ = "learning_progress"

    progress_id: Mapped[int] = mapped_column(primary_key=True)

    # Cascades, like SimulationSession: progress is personal and has no
    # meaning detached from the user.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    module_name: Mapped[str] = mapped_column(String(120), nullable=False)

    comp_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DEFAULT_STATUS,
        server_default=DEFAULT_STATUS,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Null unless comp_status is 'completed' -- enforced below.
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="progress")

    __table_args__ = (
        # See decision 1 -- one record per user per module.
        UniqueConstraint(
            "user_id", "module_name", name="uq_progress_user_module"
        ),
        CheckConstraint(
            "comp_status IN ('" + "', '".join(COMPLETION_STATUSES) + "')",
            name="ck_progress_status_valid",
        ),
        # See decision 3 -- both directions.
        CheckConstraint(
            "(comp_status = 'completed' AND completed_at IS NOT NULL) "
            "OR (comp_status != 'completed' AND completed_at IS NULL)",
            name="ck_progress_completed_has_timestamp",
        ),
        Index("ix_progress_status", "comp_status"),
    )

    @property
    def is_complete(self) -> bool:
        return self.comp_status == COMPLETED

    def mark_complete(self, when: datetime | None = None) -> None:
        """Finish the module, stamping the time.

        The timestamp is set BEFORE the status, and that order matters.
        The CHECK constraint requires the two to agree, and SQLAlchemy's
        autoflush can emit an UPDATE between two assignments -- so setting
        the status first briefly puts the row in the forbidden state
        (completed, no timestamp) and the flush fails with
        `CHECK constraint failed: ck_progress_completed_has_timestamp`.

        Found by test_mark_complete_moves_both_fields, which is exactly the
        kind of ordering bug that would otherwise surface only under load.
        """
        if self.completed_at is None:
            self.completed_at = when or datetime.now()
        self.comp_status = COMPLETED

    def __repr__(self) -> str:
        return (
            f"LearningProgress(progress_id={self.progress_id}, "
            f"user_id={self.user_id}, module={self.module_name!r}, "
            f"status={self.comp_status!r})"
        )
