"""SafeSuggestion model.

Task 46. The rewritten, safe version of an attacking prompt, shown to the
user as teaching material. Feeds `safePromptSuggestion` in the API contract.

OVERLAP WITH Task 45 -- READ THIS BEFORE WRITING Task 56 OR 57.

`MitigationAction` with `action_type='rewriting'` also stores a rewritten
prompt, in `mitigated_prompt`. Two tables can therefore hold "a safer
version of this prompt", and without a rule Task 56 would have two places
to read `safePromptSuggestion` from and could pick differently in different
endpoints.

The split, which the plan implies and this module makes explicit:

    MitigationAction.mitigated_prompt   what the system DID
                                        an audit record; append-only; several
                                        per analysis; answers "what action was
                                        taken and when"

    SafeSuggestion.suggested_prompt     what the user SHOULD HAVE WRITTEN
                                        teaching material; one current
                                        suggestion per analysis; answers "show
                                        me a better prompt"

So: **the API's `safePromptSuggestion` field reads from this table.** A
`rewriting` MitigationAction is written at the same time when the system
actually substituted the text, and the two will often agree -- but one is a
log entry and the other is advice, and they are not interchangeable.

THREE OTHER DECISIONS:

1. analysis_id IS UNIQUE.

   One current suggestion per analysis. Without it, re-running the rewrite
   logic appends a second row and the API has to guess which to return.
   Regenerating should update this row.

2. suggestion_reason IS NOT NULL.

   The whole point of this project is teaching secure prompting. A
   suggestion with no explanation of *why* it is safer is a rewrite, not a
   lesson, and the avatar in Task 47 has nothing to narrate.

3. suggested_prompt MUST DIFFER FROM NOTHING -- IT IS SIMPLY REQUIRED.

   No CHECK compares it to the original, because the original lives on
   another table and a cross-table CHECK is not portable. Task 57 should
   refuse to store a suggestion identical to the input.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis import AnalysisResult


class SafeSuggestion(Base):
    """A safer rewrite of an attacking prompt, with the reasoning."""

    __tablename__ = "safe_suggestions"

    suggestion_id: Mapped[int] = mapped_column(primary_key=True)

    # Unique -- one current suggestion per analysis. See decision 1.
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_results.analysis_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Text, not String: a rewrite is as long as the original, which the ML
    # work measured up to ~3,900 tokens.
    suggested_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Required -- see decision 2. Without the reasoning this is a rewrite
    # rather than a lesson.
    suggestion_reason: Mapped[str] = mapped_column(Text, nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    analysis: Mapped["AnalysisResult"] = relationship(
        "AnalysisResult", back_populates="suggestion"
    )

    def __repr__(self) -> str:
        # The suggestion is derived from user content; do not render it in
        # full, since repr() lands in logs.
        return (
            f"SafeSuggestion(suggestion_id={self.suggestion_id}, "
            f"analysis_id={self.analysis_id})"
        )
