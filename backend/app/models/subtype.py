"""AttackSubtype model.

Task 44. Stores the 8-class sub-type prediction from the stretch-goal
classifier in ML Task 34, alongside the 3-class result in Task 43.

FIVE DECISIONS:

1. SUBTYPE_NAMES IS DUPLICATED FROM ml/training/subtype_dataset.py.

   Same reasoning as Task 43's PROMPT_TYPES: importing would pull torch into
   the API process. A test parses the ML file and fails if the two sets ever
   diverge, in either direction.

2. SUB-TYPES ARE CONSTRAINED TO THEIR PARENT CLASS.

   "Policy Evasion" under an Indirect Injection analysis is nonsense, but
   nothing in a plain CHECK on subtype_name alone would stop it. The
   SUBTYPE_PARENT mapping records which class each belongs to, and
   `is_valid_for()` lets Task 56 reject a mismatch before it is stored.

   This is not enforced by the database, because the parent class lives on
   another table and a CHECK cannot cross tables portably. It is enforced at
   the write path instead, with the mapping as the single source.

3. analysis_id IS NULLABLE, PER THE PLAN -- BUT UNIQUE WHEN SET.

   The plan specifies nullable. Kept, since a sub-type may be recorded
   during simulation seeding (Task 62) before any analysis exists. Unique so
   one analysis cannot accumulate several sub-type rows and make the
   dashboard count one attack as many.

4. confidence IS SEPARATE FROM THE 3-CLASS CONFIDENCE, AND NULLABLE.

   The sub-type head is a *different model* with its own softmax. Storing
   its probability in the same column as the 3-class confidence would
   conflate two unrelated numbers. Nullable because a sub-type can be
   recorded without the model having produced a probability.

5. ROLE OVERRIDE IS RECORDED AS UNRELIABLE.

   ML Task 34 measured the sub-type head at 0.0000 F1 on Role Override --
   it is never predicted, 0 of 18 on the held-out test set, with 14 of those
   landing as Policy Evasion. So a stored "Policy Evasion" may in fact be
   Role Override.

   UNRELIABLE_SUBTYPES carries that fact into the backend so Task 56 and the
   UI can qualify it, rather than presenting a sub-type with the same
   authority as the 3-class label. See ml/MODEL_CARD.md section 19.7.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis import AnalysisResult

# MUST match ml/training/subtype_dataset.py SUBTYPES. A test enforces it.
SUBTYPE_NAMES = (
    "Policy Evasion",
    "Multi-Turn Manipulation",
    "Role Override",
    "Persona Hijacking",
    "System Prompt Overwrite",
    "Document Embedding",
    "Web Content Injection",
    "Tool Output Injection",
)

# Which 3-class label each sub-type belongs under -- see decision 2.
SUBTYPE_PARENT = {
    "Policy Evasion": "Direct Jailbreak",
    "Multi-Turn Manipulation": "Direct Jailbreak",
    "Role Override": "Direct Jailbreak",
    "Persona Hijacking": "Direct Jailbreak",
    "System Prompt Overwrite": "Direct Jailbreak",
    "Document Embedding": "Indirect Injection",
    "Web Content Injection": "Indirect Injection",
    "Tool Output Injection": "Indirect Injection",
}

# Sub-types the ML model cannot reliably identify -- see decision 5 and
# ml/MODEL_CARD.md 19.7. A prediction of a *different* sub-type may in fact
# be one of these.
UNRELIABLE_SUBTYPES = {
    "Role Override": (
        "The sub-type classifier scores 0.00 F1 on Role Override and never "
        "predicts it (0 of 18 on the held-out test set). 14 of those 18 were "
        "classified as Policy Evasion, so a stored sub-type may be wrong in "
        "that direction. Trained on only 83 examples."
    ),
}


def is_valid_for(subtype_name: str, prompt_type: str) -> bool:
    """True if this sub-type belongs under that 3-class label.

    Task 56 should call this before storing, so an impossible pairing is
    rejected at the API rather than persisted.
    """
    return SUBTYPE_PARENT.get(subtype_name) == prompt_type


class AttackSubtype(Base):
    """The 8-class sub-type prediction for one analysis."""

    __tablename__ = "attack_subtypes"

    subtype_id: Mapped[int] = mapped_column(primary_key=True)

    # Nullable per the plan; unique so one analysis cannot accumulate
    # several rows -- see decision 3.
    analysis_id: Mapped[int | None] = mapped_column(
        ForeignKey("analysis_results.analysis_id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )

    subtype_name: Mapped[str] = mapped_column(String(40), nullable=False)

    type_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The sub-type head's own softmax -- a different model from the 3-class
    # one, so a separate column. See decision 4.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    analysis: Mapped["AnalysisResult | None"] = relationship(
        "AnalysisResult", back_populates="subtype"
    )

    __table_args__ = (
        CheckConstraint(
            "subtype_name IN ('" + "', '".join(SUBTYPE_NAMES) + "')",
            name="ck_subtype_name_valid",
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)",
            name="ck_subtype_confidence_range",
        ),
        Index("ix_subtype_name", "subtype_name"),
    )

    @property
    def is_reliable(self) -> bool:
        """False when the ML model cannot identify this sub-type.

        Task 56 and the UI should qualify an unreliable sub-type rather than
        presenting it with the same authority as the 3-class label.
        """
        return self.subtype_name not in UNRELIABLE_SUBTYPES

    @property
    def reliability_note(self) -> str | None:
        return UNRELIABLE_SUBTYPES.get(self.subtype_name)

    def __repr__(self) -> str:
        return (
            f"AttackSubtype(subtype_id={self.subtype_id}, "
            f"analysis_id={self.analysis_id}, name={self.subtype_name!r}, "
            f"reliable={self.is_reliable})"
        )
