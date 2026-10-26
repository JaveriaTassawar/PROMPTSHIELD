"""Tests for the Task 48 SimulationSession and Task 49 LearningProgress.

Three tests cover constraints that prevent corrupt analytics rather than
crashes: a session ending before it starts (negative durations), a module
marked complete with no completion date (inflated completion rates), and a
duplicate progress row per module (a progress bar reading over 100%).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import app.core.database  # noqa: F401  -- registers the FK pragma listener
from app.core.database import Base
from app.models.progress import (
    COMPLETION_STATUSES,
    LearningProgress,
)
from app.models.simulation import (
    DIFFICULTY_LEVELS,
    SIMULATION_OUTCOMES,
    SimulationSession,
)
from app.models.user import User

FAKE_HASH = "$2b$12$" + "x" * 53


@pytest.fixture
def db(tmp_path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def user(db: Session) -> User:
    account = User(
        user_name="Jawaria", email="j@ucp.edu.pk", password_hash=FAKE_HASH
    )
    db.add(account)
    db.commit()
    return account


# --- SimulationSession (Task 48) -------------------------------------------


def test_session_starts_in_progress(db: Session, user: User) -> None:
    """NULL outcome is a real state, distinct from 'abandoned'."""
    session = SimulationSession(
        user_id=user.user_id, scenario_name="Spot the injection"
    )
    db.add(session)
    db.commit()

    assert session.outcome is None
    assert session.is_in_progress is True
    assert session.end_time is None
    assert session.difficulty == "Beginner"


@pytest.mark.parametrize("outcome", SIMULATION_OUTCOMES)
def test_every_outcome_is_accepted(
    db: Session, user: User, outcome: str
) -> None:
    session = SimulationSession(
        user_id=user.user_id, scenario_name="s", outcome=outcome
    )
    db.add(session)
    db.commit()
    assert db.query(SimulationSession).one().outcome == outcome


def test_invalid_outcome_is_rejected(db: Session, user: User) -> None:
    db.add(
        SimulationSession(
            user_id=user.user_id, scenario_name="s", outcome="finished"
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_difficulty_matches_the_frontend_labels() -> None:
    """frontend/src/config/simulation.js defines these three, so Task 62
    can seed scenarios without the frontend remapping anything."""
    assert DIFFICULTY_LEVELS == ("Beginner", "Intermediate", "Advanced")


def test_invalid_difficulty_is_rejected(db: Session, user: User) -> None:
    db.add(
        SimulationSession(
            user_id=user.user_id, scenario_name="s", difficulty="Expert"
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_session_cannot_end_before_it_starts(
    db: Session, user: User
) -> None:
    """Catches clock problems and transposed arguments. Without the
    constraint this silently produces negative durations in Task 63."""
    now = datetime.now()
    db.add(
        SimulationSession(
            user_id=user.user_id,
            scenario_name="s",
            start_time=now,
            end_time=now - timedelta(minutes=5),
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_finish_sets_outcome_and_end_time(db: Session, user: User) -> None:
    session = SimulationSession(user_id=user.user_id, scenario_name="s")
    db.add(session)
    db.commit()

    session.finish("completed", score=8)
    db.commit()

    assert session.outcome == "completed"
    assert session.score == 8
    assert session.end_time is not None
    assert session.is_in_progress is False


def test_finish_rejects_an_unknown_outcome(
    db: Session, user: User
) -> None:
    session = SimulationSession(user_id=user.user_id, scenario_name="s")
    db.add(session)
    db.commit()

    with pytest.raises(ValueError, match="not one of"):
        session.finish("won")


def test_negative_score_is_rejected(db: Session, user: User) -> None:
    db.add(
        SimulationSession(
            user_id=user.user_id, scenario_name="s", score=-1
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_deleting_the_user_deletes_their_sessions(
    db: Session, user: User
) -> None:
    """Unlike prompts, which survive anonymised.

    A training session is personal progress with no meaning detached
    from the person; orphans would inflate completion counts for users
    who no longer exist.
    """
    db.add(SimulationSession(user_id=user.user_id, scenario_name="s"))
    db.commit()

    db.delete(user)
    db.commit()

    assert db.query(SimulationSession).count() == 0


# --- LearningProgress (Task 49) --------------------------------------------


def test_progress_defaults_to_not_started(db: Session, user: User) -> None:
    """Stored explicitly rather than as a missing row, so 'opened it' and
    'finished it' are different queries."""
    row = LearningProgress(user_id=user.user_id, module_name="Intro")
    db.add(row)
    db.commit()

    assert row.comp_status == "not_started"
    assert row.completed_at is None
    assert row.is_complete is False


@pytest.mark.parametrize("status", COMPLETION_STATUSES)
def test_every_status_is_accepted(
    db: Session, user: User, status: str
) -> None:
    row = LearningProgress(
        user_id=user.user_id,
        module_name="Intro",
        comp_status=status,
        completed_at=datetime.now() if status == "completed" else None,
    )
    db.add(row)
    db.commit()
    assert db.query(LearningProgress).one().comp_status == status


def test_invalid_status_is_rejected(db: Session, user: User) -> None:
    db.add(
        LearningProgress(
            user_id=user.user_id, module_name="Intro", comp_status="done"
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_completed_without_a_timestamp_is_rejected(
    db: Session, user: User
) -> None:
    """Otherwise Task 63 counts it as finished with no date."""
    db.add(
        LearningProgress(
            user_id=user.user_id,
            module_name="Intro",
            comp_status="completed",
            completed_at=None,
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_unfinished_with_a_timestamp_is_rejected(
    db: Session, user: User
) -> None:
    """The other direction: in_progress must not carry a completion date."""
    db.add(
        LearningProgress(
            user_id=user.user_id,
            module_name="Intro",
            comp_status="in_progress",
            completed_at=datetime.now(),
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()


def test_mark_complete_moves_both_fields(db: Session, user: User) -> None:
    """They must move together -- the CHECK rejects setting one alone."""
    row = LearningProgress(user_id=user.user_id, module_name="Intro")
    db.add(row)
    db.commit()

    row.mark_complete()
    db.commit()

    assert row.is_complete is True
    assert row.completed_at is not None


def test_one_progress_row_per_user_per_module(
    db: Session, user: User
) -> None:
    """Without this, re-opening a module appends a row and every
    completion count inflates -- a progress bar reading over 100%."""
    db.add(LearningProgress(user_id=user.user_id, module_name="Intro"))
    db.commit()

    db.add(LearningProgress(user_id=user.user_id, module_name="Intro"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_same_module_for_different_users_is_fine(db: Session) -> None:
    for name in ("a", "b"):
        account = User(
            user_name=name,
            email=f"{name}@ucp.edu.pk",
            password_hash=FAKE_HASH,
        )
        db.add(account)
        db.commit()
        db.add(
            LearningProgress(user_id=account.user_id, module_name="Intro")
        )
        db.commit()

    assert db.query(LearningProgress).count() == 2


def test_deleting_the_user_deletes_their_progress(
    db: Session, user: User
) -> None:
    db.add(LearningProgress(user_id=user.user_id, module_name="Intro"))
    db.commit()

    db.delete(user)
    db.commit()

    assert db.query(LearningProgress).count() == 0


def test_both_models_are_registered_for_autogenerate() -> None:
    import app.models

    assert "simulation_sessions" in Base.metadata.tables
    assert "learning_progress" in Base.metadata.tables
    assert hasattr(app.models, "SimulationSession")
    assert hasattr(app.models, "LearningProgress")
