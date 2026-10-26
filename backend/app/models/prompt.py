"""Prompt model.

Task 42. One row per prompt a user submits to the analyzer. Task 43's
AnalysisResult hangs off it, and the analytics in Tasks 60-63 aggregate
over it.

FOUR DECISIONS:

1. prompt_text IS Text, NOT String(n).

   The ML work measured real attack prompts at up to 3,923 tokens, with
   Persona Hijacking averaging over a thousand. A VARCHAR limit would
   truncate exactly the long multi-turn and persona attacks the classifier
   is weakest on, and the truncation happens silently on MySQL. Text has no
   practical ceiling on any of the three backends.

   No length cap is enforced here on purpose -- the API layer (Task 56)
   should reject oversized input with a 422 before it reaches the database,
   where the error would be a 500 instead.

2. THE USER FK IS ondelete="SET NULL", AND user_id IS NULLABLE.

   Deleting a user must not delete their prompts. The analytics in Tasks
   60-63 aggregate over historical prompts, and CASCADE would silently
   rewrite past totals the moment an account was removed. SET NULL keeps the
   row and anonymises it.

   Task 41's `is_active` is the preferred path anyway -- deactivate rather
   than delete. This is the fallback for when a row really is removed.

3. status IS CHECK-CONSTRAINED, like User.role.

   A typo writes fine into a free string column and leaves a prompt stuck in
   a state no query matches -- invisible until someone notices the dashboard
   count is wrong.

4. THE (user_id, submission_time) INDEX IS DELIBERATE.

   The dashboard (Task 60) and history (Task 58) both ask "this user's
   prompts, newest first". A composite index serves that directly; two
   single-column indexes do not.
"""

from __future__ import annotations

from datetime import datetime

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

# A prompt is created `pending`, becomes `analyzed` once Task 56 classifies
# it, or `blocked` if mitigation (Task 57) refuses it outright.
PROMPT_STATUSES = ("pending", "analyzed", "blocked")
DEFAULT_STATUS = "pending"


class Prompt(Base):
    """One submitted prompt, awaiting or carrying an analysis."""

    __tablename__ = "prompts"

    prompt_id: Mapped[int] = mapped_column(primary_key=True)

    # Nullable by design -- see decision 2.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # See decision 1. Real attacks run to thousands of characters.
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)

    submission_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DEFAULT_STATUS,
        server_default=DEFAULT_STATUS,
    )

    user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="prompts"
    )

    # One analysis per prompt (the FK is unique). Deleting the prompt
    # deletes its analysis -- an analysis with no prompt has nothing to
    # display. See AnalysisResult decision 4.
    analysis: Mapped["AnalysisResult | None"] = relationship(  # noqa: F821
        "AnalysisResult",
        back_populates="prompt",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('" + "', '".join(PROMPT_STATUSES) + "')",
            name="ck_prompts_status_valid",
        ),
        # See decision 4 -- serves "this user's prompts, newest first".
        Index("ix_prompts_user_time", "user_id", "submission_time"),
        Index("ix_prompts_status", "status"),
    )

    def __repr__(self) -> str:
        # Prompt text is user content and may be an attack payload; never
        # render it in full. repr() lands in logs.
        preview = (self.prompt_text or "")[:40]
        suffix = "..." if self.prompt_text and len(self.prompt_text) > 40 else ""
        return (
            f"Prompt(prompt_id={self.prompt_id}, user_id={self.user_id}, "
            f"status={self.status!r}, text={preview!r}{suffix})"
        )
