"""AnalysisResult model.

Task 43. One row per classification. This is where the backend meets the ML
track: `prompt_type` stores the label `ml/inference/classifier.py` returns.

FIVE DECISIONS:

1. PROMPT_TYPES IS COPIED FROM THE ML LABEL SET, DELIBERATELY DUPLICATED.

   `ml/training/dataset.py` pins LABEL2ID as the authoritative mapping. The
   backend cannot import it -- that would make the API depend on torch and
   pandas, turning a 30 MB service into a 2 GB one and making every endpoint
   wait on a model import.

   So the three strings are restated here, with a test that fails if the two
   lists ever diverge. Duplication with a guard beats either a heavyweight
   import or a silent mismatch where the classifier returns a label the
   database refuses.

2. confidence_score IS CHECK-CONSTRAINED TO 0..1.

   The classifier returns a softmax probability. A bug that wrote a
   percentage (94.0 instead of 0.94) would not fail anywhere -- it would
   just make every confidence display and every analytics average wrong, in
   a way that looks plausible until someone checks. The database refuses it.

3. prompt_id IS UNIQUE.

   One prompt gets one analysis. Without the constraint, re-running analysis
   silently appends a second row and the dashboard counts every prompt
   twice. Re-analysis should update the existing row, and the constraint
   forces that to be a deliberate choice.

4. THE PROMPT FK CASCADES, UNLIKE Prompt -> User.

   An analysis without its prompt is meaningless -- there is nothing to
   display and no text to explain. That differs from Task 42, where the
   prompt survives its user on purpose, and the asymmetry is intentional:
   the prompt is the thing of record, the analysis is derived from it.

5. severity_level IS DEFINED HERE.

   The plan only shows "High" in one sample response and never enumerates
   the set. Four levels are defined below; if the frontend or SRS pins a
   different vocabulary, this constraint is the single place to change.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.prompt import Prompt

# MUST match ml/training/dataset.py LABEL2ID. See decision 1 -- a test
# enforces this rather than trusting the comment.
PROMPT_TYPES = ("Safe", "Direct Jailbreak", "Indirect Injection")

# See decision 5. Not pinned by the SRS; defined here as the single source.
SEVERITY_LEVELS = ("Low", "Medium", "High", "Critical")

# Severity implied by classification when the caller does not supply one.
# Safe is always Low; attacks default to High and may be downgraded by the
# mitigation logic in Task 57.
DEFAULT_SEVERITY_BY_TYPE = {
    "Safe": "Low",
    "Direct Jailbreak": "High",
    "Indirect Injection": "High",
}


class AnalysisResult(Base):
    """The classifier's verdict on one prompt."""

    __tablename__ = "analysis_results"

    analysis_id: Mapped[int] = mapped_column(primary_key=True)

    # Unique: one analysis per prompt -- see decision 3.
    # Cascades: an analysis without its prompt is meaningless -- decision 4.
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.prompt_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # True when the prompt was classified as an attack. Redundant with
    # prompt_type != 'Safe', but stored so the dashboard can filter on a
    # boolean without string comparison, and so the meaning survives if the
    # taxonomy ever grows a fourth class.
    detection_result: Mapped[bool] = mapped_column(nullable=False)

    prompt_type: Mapped[str] = mapped_column(String(32), nullable=False)

    severity_level: Mapped[str] = mapped_column(String(16), nullable=False)

    # Softmax probability from the classifier, 0..1 -- see decision 2.
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Free-form note from the mitigation layer (Task 57), e.g. why a prompt
    # was blocked. Text rather than String because it may quote the prompt.
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    prompt: Mapped["Prompt"] = relationship(
        "Prompt", back_populates="analysis"
    )

    __table_args__ = (
        CheckConstraint(
            "prompt_type IN ('" + "', '".join(PROMPT_TYPES) + "')",
            name="ck_analysis_prompt_type_valid",
        ),
        CheckConstraint(
            "severity_level IN ('" + "', '".join(SEVERITY_LEVELS) + "')",
            name="ck_analysis_severity_valid",
        ),
        CheckConstraint(
            "confidence_score >= 0.0 AND confidence_score <= 1.0",
            name="ck_analysis_confidence_range",
        ),
        # Tasks 60-63 aggregate "how many of each class, over time".
        Index("ix_analysis_type_time", "prompt_type", "analysed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"AnalysisResult(analysis_id={self.analysis_id}, "
            f"prompt_id={self.prompt_id}, type={self.prompt_type!r}, "
            f"severity={self.severity_level!r}, "
            f"confidence={self.confidence_score})"
        )
