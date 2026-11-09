"""SimulationSession model.

Task 48. One run of a user through an avatar-guided practice scenario --
the "simulation-based learning" half of the project title.

FOUR DECISIONS:

1. outcome IS NULLABLE AND CHECK-CONSTRAINED.

   A session in progress has no outcome yet, so NULL is a real state:
   "started, not finished". Distinguishing that from `abandoned` matters --
   one is a user still working, the other is a user who gave up, and the
   Tasks 60-63 analytics should not conflate them.

   Values are constrained for the same reason as every other status column
   in this schema: a typo leaves a session in a state no query matches.

2. end_time IS NULLABLE, AND MUST NOT PRECEDE start_time.

   Null while in progress. The CHECK catches clock problems and argument
   transposition -- a session that ended before it began is a bug, and
   without the constraint it silently produces negative durations in the
   analytics.

3. difficulty MATCHES THE FRONTEND'S EXISTING LABELS.

   frontend/src/config/simulation.js already defines Beginner /
   Intermediate / Advanced and notes "Backend Task 62 may replace it".
   Using the same three strings means Task 62 can seed scenarios without
   the frontend needing to remap anything.

4. user_id CASCADES, UNLIKE Prompt -> User.

   Deliberate difference. A prompt is evidence and survives its user
   anonymised, because the analytics aggregate over prompts. A training
   session is personal progress -- it has no meaning detached from the
   person who ran it, and keeping orphaned sessions would inflate
   completion counts for users who no longer exist.
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
    from app.models.user import User

# NULL means in progress -- see decision 1.
SIMULATION_OUTCOMES = ("completed", "failed", "abandoned")

# Matches frontend/src/config/simulation.js TRAINING_DIFFICULTY.
DIFFICULTY_LEVELS = ("Beginner", "Intermediate", "Advanced")
DEFAULT_DIFFICULTY = "Beginner"


class SimulationSession(Base):
    """One user's run through one practice scenario."""

    __tablename__ = "simulation_sessions"

    simulation_id: Mapped[int] = mapped_column(primary_key=True)

    # Cascades -- see decision 4.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scenario_name: Mapped[str] = mapped_column(String(120), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    difficulty: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DEFAULT_DIFFICULTY,
        server_default=DEFAULT_DIFFICULTY,
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Null while the session is still running -- see decision 2.
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Null means in progress, not "no result".
    outcome: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # How many prompts the user got right. Nullable because a scenario may
    # not be scored.
    score: Mapped[int | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(
        "User", back_populates="simulations"
    )

    __table_args__ = (
        CheckConstraint(
            "outcome IS NULL OR outcome IN ('"
            + "', '".join(SIMULATION_OUTCOMES)
            + "')",
            name="ck_simulation_outcome_valid",
        ),
        CheckConstraint(
            "difficulty IN ('" + "', '".join(DIFFICULTY_LEVELS) + "')",
            name="ck_simulation_difficulty_valid",
        ),
        # See decision 2 -- a session cannot end before it started.
        CheckConstraint(
            "end_time IS NULL OR end_time >= start_time",
            name="ck_simulation_end_after_start",
        ),
        CheckConstraint(
            "score IS NULL OR score >= 0",
            name="ck_simulation_score_non_negative",
        ),
        # Task 60's "my recent sessions" and Task 63's completion rates.
        Index("ix_simulation_user_start", "user_id", "start_time"),
        Index("ix_simulation_outcome", "outcome"),
    )

    @property
    def is_in_progress(self) -> bool:
        """True while started but not yet resolved."""
        return self.outcome is None

    def finish(self, outcome: str, score: int | None = None) -> None:
        """Close the session. Stamps end_time if it is not already set."""
        if outcome not in SIMULATION_OUTCOMES:
            raise ValueError(
                f"{outcome!r} is not one of {SIMULATION_OUTCOMES}"
            )
        self.outcome = outcome
        if score is not None:
            self.score = score
        if self.end_time is None:
            self.end_time = datetime.now()

    def __repr__(self) -> str:
        state = self.outcome or "in progress"
        return (
            f"SimulationSession(simulation_id={self.simulation_id}, "
            f"user_id={self.user_id}, scenario={self.scenario_name!r}, "
            f"state={state!r})"
        )
