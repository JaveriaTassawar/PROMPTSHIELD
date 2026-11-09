"""Simulation scenario models.

Task 62. Reference content for the Simulation Lab -- hand-authored
training scripts, not user data.

WHY THESE TABLES EXIST AT ALL.

The plan never specified a Scenario model, and Task 48's
`SimulationSession` only stores `scenario_name` and `description` as free
text on each run. That is enough to record *that* someone ran a scenario,
but not to serve the scenario itself: Task 83's picker needs a catalogue,
and Task 84 needs each scenario's turns.

The alternative was a Python constant. Rejected because adding or
correcting a scenario would then need a code change and a redeploy, and
because `SimulationSession.scenario_id` can now reference a real row
instead of matching on a name string.

THREE DECISIONS:

1. `slug` IS THE PUBLIC IDENTIFIER, NOT THE INTEGER ID.

   The frontend catalogue already uses string ids -- 'unrestricted-persona',
   'poisoned-document'. URLs in Task 83 are /simulation/:scenarioId, and a
   readable slug there survives a reseed, whereas an autoincrement id does
   not. `scenario_id` stays as the foreign-key target.

2. TURNS ARE A SEPARATE TABLE, ORDERED EXPLICITLY.

   A scenario is a conversation, and the order carries the lesson -- a
   Multi-Turn Manipulation script is meaningless shuffled. `position`
   makes the order data rather than an artefact of insertion, and the
   unique constraint on (scenario, position) stops two turns claiming
   the same slot.

3. `is_attack` IS PER TURN, NOT PER SCENARIO.

   In a multi-turn script the early turns are genuinely harmless; that is
   the point of the scenario. A single scenario-level flag could not
   express "turn 3 is where this becomes an attack", which is exactly
   what the user is being taught to spot.
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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.simulation import DIFFICULTY_LEVELS

if TYPE_CHECKING:
    pass

# Where a turn's content comes from. Matches TURN_ROLES in
# frontend/src/config/simulation.js, which the UI already renders:
# `external` content is shown in monospace so it can be inspected.
TURN_ROLES = ("user", "document", "tool", "web")

# Roles whose content the AI system consumes rather than the user typing.
# These are the vectors for Indirect Injection.
EXTERNAL_ROLES = frozenset({"document", "tool", "web"})


class Scenario(Base):
    """One hand-authored training scenario."""

    __tablename__ = "scenarios"

    scenario_id: Mapped[int] = mapped_column(primary_key=True)

    # Public identifier -- see decision 1.
    slug: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True, index=True
    )

    # Display code, e.g. SIM-01. Not the identifier: renumbering the
    # catalogue should not break a URL.
    code: Mapped[str] = mapped_column(String(16), nullable=False)

    title: Mapped[str] = mapped_column(String(120), nullable=False)

    # The sub-type this scenario teaches. Not a foreign key -- sub-types
    # are a fixed taxonomy in code, not a table.
    subtype: Mapped[str] = mapped_column(String(40), nullable=False)

    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)

    # What the learner should take away. Required: a scenario with no
    # stated objective is a demo, not a lesson.
    objective: Mapped[str] = mapped_column(Text, nullable=False)

    # Lets a scenario be retired without deleting it, which would orphan
    # the sessions that reference it.
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="1"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    turns: Mapped[list["ScenarioTurn"]] = relationship(
        "ScenarioTurn",
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="ScenarioTurn.position",
    )

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('" + "', '".join(DIFFICULTY_LEVELS) + "')",
            name="ck_scenario_difficulty_valid",
        ),
        Index("ix_scenario_subtype", "subtype"),
    )

    @property
    def attack_turn_positions(self) -> list[int]:
        """Which turns are the attack. Usually what the lesson is about."""
        return [t.position for t in self.turns if t.is_attack]

    def __repr__(self) -> str:
        return (
            f"Scenario(scenario_id={self.scenario_id}, slug={self.slug!r}, "
            f"subtype={self.subtype!r}, turns={len(self.turns)})"
        )


class ScenarioTurn(Base):
    """One turn in a scenario's conversation."""

    __tablename__ = "scenario_turns"

    turn_id: Mapped[int] = mapped_column(primary_key=True)

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenarios.scenario_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Order is data, not insertion order -- see decision 2.
    position: Mapped[int] = mapped_column(nullable=False)

    role: Mapped[str] = mapped_column(String(20), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Per turn, not per scenario -- see decision 3.
    is_attack: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="0"
    )

    # The scenario's own teaching note for this turn. Nullable: a
    # harmless setup turn may need no comment.
    annotation: Mapped[str | None] = mapped_column(Text, nullable=True)

    scenario: Mapped["Scenario"] = relationship(
        "Scenario", back_populates="turns"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('" + "', '".join(TURN_ROLES) + "')",
            name="ck_turn_role_valid",
        ),
        CheckConstraint("position >= 1", name="ck_turn_position_positive"),
        # Two turns must not claim the same slot -- see decision 2.
        UniqueConstraint(
            "scenario_id", "position", name="uq_turn_scenario_position"
        ),
    )

    @property
    def is_external(self) -> bool:
        """True when the content is consumed rather than typed.

        These are the Indirect Injection vectors, and the frontend shows
        them in monospace so they can be inspected.
        """
        return self.role in EXTERNAL_ROLES

    def __repr__(self) -> str:
        return (
            f"ScenarioTurn(turn_id={self.turn_id}, position={self.position}, "
            f"role={self.role!r}, is_attack={self.is_attack})"
        )
