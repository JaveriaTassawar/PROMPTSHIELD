"""Tests for Task 62 (seeded sandbox scenarios).

The valuable tests here are about the seed being safe to re-run and the
content being safe to ship:

  - seeding twice must not duplicate, or every reseed inflates the
    catalogue and Task 83's picker shows the same scenario repeatedly

  - the seeded attack text must not contain a genuinely harmful ask.
    Shipping working payloads in the repo would mean a user who copied
    one out of the training UI has a working attack.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.core.database  # noqa: F401  -- registers the SQLite FK pragma
from app.core.database import Base
from app.models.scenario import (
    EXTERNAL_ROLES,
    TURN_ROLES,
    Scenario,
    ScenarioTurn,
)
from app.models.simulation import DIFFICULTY_LEVELS, SimulationSession
from app.models.subtype import SUBTYPE_NAMES
from app.models.user import User
from app.seed.scenarios import SCENARIOS, seed_scenarios

FAKE_HASH = "$2b$12$" + "x" * 53


@pytest.fixture
def db(tmp_path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'scen.db'}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# --- the seed data itself --------------------------------------------------


def test_plan_asks_for_three_to_five() -> None:
    assert 3 <= len(SCENARIOS) <= 5


def test_every_scenario_uses_a_real_subtype() -> None:
    """A typo here would make Task 83's picker filter on nothing."""
    for spec in SCENARIOS:
        assert spec["subtype"] in SUBTYPE_NAMES, spec["slug"]


def test_every_scenario_uses_a_real_difficulty() -> None:
    """These must match the frontend's TRAINING_DIFFICULTY labels."""
    for spec in SCENARIOS:
        assert spec["difficulty"] in DIFFICULTY_LEVELS, spec["slug"]


def test_scenarios_cover_both_attack_classes() -> None:
    """A spread, per the plan -- not five variations on one theme."""
    from app.models.subtype import SUBTYPE_PARENT

    parents = {SUBTYPE_PARENT[s["subtype"]] for s in SCENARIOS}
    assert parents == {"Direct Jailbreak", "Indirect Injection"}


def test_slugs_and_codes_are_unique() -> None:
    slugs = [s["slug"] for s in SCENARIOS]
    codes = [s["code"] for s in SCENARIOS]
    assert len(set(slugs)) == len(slugs)
    assert len(set(codes)) == len(codes)


def test_every_scenario_has_an_objective() -> None:
    """A scenario with no stated objective is a demo, not a lesson."""
    for spec in SCENARIOS:
        assert spec["objective"].strip(), spec["slug"]


def test_every_scenario_has_at_least_one_attack_turn() -> None:
    """Otherwise there is nothing to spot."""
    for spec in SCENARIOS:
        assert any(t[3] for t in spec["turns"]), spec["slug"]


def test_turn_positions_start_at_one_and_are_contiguous() -> None:
    for spec in SCENARIOS:
        positions = sorted(t[0] for t in spec["turns"])
        assert positions == list(range(1, len(positions) + 1)), spec["slug"]


def test_every_turn_declares_provenance() -> None:
    """Marking authored text as dataset-sourced would overstate the
    evidence behind a scenario."""
    from app.models.scenario import TURN_ORIGINS

    for spec in SCENARIOS:
        for turn in spec["turns"]:
            assert turn[2] in TURN_ORIGINS, f"{spec['slug']} turn {turn[0]}"


def test_every_turn_role_is_valid() -> None:
    for spec in SCENARIOS:
        for turn in spec["turns"]:
            assert turn[1] in TURN_ROLES, f"{spec['slug']} turn {turn[0]}"


def test_attack_turns_carry_an_annotation() -> None:
    """The annotation is the lesson. An unexplained attack turn teaches
    nothing."""
    for spec in SCENARIOS:
        for position, _role, _origin, is_attack, annotation, _content in spec["turns"]:
            if is_attack:
                assert annotation and annotation.strip(), (
                    f"{spec['slug']} turn {position} is an attack with no "
                    f"annotation"
                )


def test_multi_turn_scenario_has_harmless_early_turns() -> None:
    """The point of a Multi-Turn scenario is that no single early turn is
    an attack. If every turn were flagged, it would teach nothing about
    escalation."""
    multi = next(
        s for s in SCENARIOS if s["subtype"] == "Multi-Turn Manipulation"
    )
    flags = [t[3] for t in sorted(multi["turns"], key=lambda t: t[0])]

    assert len(flags) >= 3, "escalation needs several turns to be visible"
    assert flags[0] is False, "the opening turn should be genuinely harmless"
    assert flags[-1] is True, "the escalation should end in an attack"


def test_indirect_scenarios_put_the_attack_in_external_content() -> None:
    """That is what makes them indirect: the user did not type it."""
    from app.models.subtype import SUBTYPE_PARENT

    for spec in SCENARIOS:
        if SUBTYPE_PARENT[spec["subtype"]] != "Indirect Injection":
            continue
        attack_roles = {t[1] for t in spec["turns"] if t[3]}
        assert attack_roles <= EXTERNAL_ROLES, (
            f"{spec['slug']}: an indirect attack should arrive in external "
            f"content, not a user turn (got {attack_roles})"
        )


def test_role_override_is_absent_and_that_is_deliberate() -> None:
    """ML Task 34 measured the sub-type classifier at 0.00 F1 on Role
    Override -- never predicted. A scenario teaching users to spot a
    category our own model cannot identify would teach against the tool.

    This test exists so removing the omission is a deliberate act rather
    than an accident.
    """
    subtypes = {s["subtype"] for s in SCENARIOS}
    assert "Role Override" not in subtypes


def test_seeded_payloads_are_defanged() -> None:
    """Realistic shape, harmless ask.

    Shipping working attack payloads in seeded content would mean the
    repository itself carries them, and a user who copied one out of the
    training UI would have a working attack.
    """
    forbidden = (
        "password", "credit card", "ssn", "social security",
        "api key", "private key", "exploit", "malware", "ransomware",
    )
    for spec in SCENARIOS:
        for position, _role, _origin, _is_attack, _annotation, content in spec["turns"]:
            lowered = content.lower()
            for term in forbidden:
                assert term not in lowered, (
                    f"{spec['slug']} turn {position} asks for {term!r} -- "
                    f"seeded attack text must be defanged"
                )


# --- seeding ---------------------------------------------------------------


def test_seed_creates_everything(db: Session) -> None:
    created, updated = seed_scenarios(db)

    assert created == len(SCENARIOS)
    assert updated == 0
    assert db.scalar(select(Scenario).where(Scenario.slug == "poisoned-document"))


def test_seed_is_idempotent(db: Session) -> None:
    """Re-running must update, not duplicate. Otherwise every reseed
    inflates the catalogue and Task 83's picker repeats itself."""
    seed_scenarios(db)
    before_scenarios = db.query(Scenario).count()
    before_turns = db.query(ScenarioTurn).count()

    created, updated = seed_scenarios(db)

    assert created == 0
    assert updated == len(SCENARIOS)
    assert db.query(Scenario).count() == before_scenarios
    assert db.query(ScenarioTurn).count() == before_turns


def test_turns_come_back_in_order(db: Session) -> None:
    """A Multi-Turn script shuffled is meaningless."""
    seed_scenarios(db)

    scenario = db.scalar(
        select(Scenario).where(Scenario.slug == "gradual-escalation")
    )
    positions = [t.position for t in scenario.turns]

    assert positions == sorted(positions)
    assert positions == list(range(1, len(positions) + 1))


# --- model constraints -----------------------------------------------------


def test_two_turns_cannot_share_a_position(db: Session) -> None:
    seed_scenarios(db)
    scenario = db.scalar(select(Scenario).where(Scenario.slug == "poisoned-document"))

    db.add(
        ScenarioTurn(
            scenario_id=scenario.scenario_id,
            position=1,
            role="user",
            content="duplicate position",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_invalid_turn_role_is_rejected(db: Session) -> None:
    seed_scenarios(db)
    scenario = db.scalar(select(Scenario).where(Scenario.slug == "poisoned-document"))

    db.add(
        ScenarioTurn(
            scenario_id=scenario.scenario_id,
            position=99,
            role="assistant",  # not a valid role: no turn is a model reply
            content="x",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_deleting_a_scenario_deletes_its_turns(db: Session) -> None:
    seed_scenarios(db)
    scenario = db.scalar(select(Scenario).where(Scenario.slug == "poisoned-document"))
    turn_count = len(scenario.turns)
    assert turn_count > 0

    total_before = db.query(ScenarioTurn).count()

    db.delete(scenario)
    db.commit()

    # Exactly that scenario's turns went, and no others.
    assert db.query(ScenarioTurn).count() == total_before - turn_count
    assert (
        db.query(ScenarioTurn)
        .filter(ScenarioTurn.scenario_id == scenario.scenario_id)
        .count()
        == 0
    )
    assert db.scalar(
        select(Scenario).where(Scenario.slug == "poisoned-document")
    ) is None


def test_retiring_a_scenario_keeps_the_sessions_that_ran_it(
    db: Session,
) -> None:
    """SET NULL, not CASCADE. A retired scenario must not delete the
    record that someone ran it, and the denormalised scenario_name keeps
    those sessions readable."""
    seed_scenarios(db)
    scenario = db.scalar(select(Scenario).where(Scenario.slug == "poisoned-document"))

    user = User(user_name="x", email="x@ucp.edu.pk", password_hash=FAKE_HASH)
    db.add(user)
    db.commit()

    db.add(
        SimulationSession(
            user_id=user.user_id,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.title,
        )
    )
    db.commit()

    db.delete(scenario)
    db.commit()
    db.expire_all()

    session = db.query(SimulationSession).one()
    assert session.scenario_id is None
    assert session.scenario_name == "The Poisoned Document"


def test_external_roles_are_the_indirect_vectors() -> None:
    assert EXTERNAL_ROLES == {"document", "tool", "web"}
    assert "user" not in EXTERNAL_ROLES


def test_models_are_registered_for_autogenerate() -> None:
    import app.models

    assert "scenarios" in Base.metadata.tables
    assert "scenario_turns" in Base.metadata.tables
    assert hasattr(app.models, "Scenario")
