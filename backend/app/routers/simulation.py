"""Simulation Lab endpoints.

Task 63. Three routes, because the one the plan names is unusable alone:

    GET  /api/scenarios              the catalogue (Task 83's picker)
    GET  /api/scenarios/{slug}       one scenario's turns (Task 84)
    POST /api/simulate-attack        classify one turn, record the session

FIVE DECISIONS:

1. THE TURN IS CLASSIFIED BY THE REAL MODEL, NOT READ FROM is_attack.

   Every turn already carries `is_attack` -- the author's label. Returning
   that would make the Simulation Lab a slideshow: the user would see a
   "detection" that is really a lookup, and the lab would show perfect
   accuracy even if the model were broken.

   So the turn text goes through `classify_prompt()` like any other
   prompt. The authored label is returned *alongside* as `expected`, and
   `agreed` says whether they matched. A learner seeing the model
   disagree with the script is learning something true about the model.

2. A SESSION ROW IS CREATED ON THE FIRST TURN AND REUSED AFTER.

   The plan says the endpoint writes a SimulationSession. Written per
   turn, a three-turn scenario would produce three "sessions" and the
   Tasks 60-63 completion counts would triple. The session is keyed on
   (user, scenario, still-running) and closed when the last turn is
   scanned.

3. THE SCORE COUNTS AGREEMENTS, NOT ATTACKS FOUND.

   `score` is how many turns the model classified as the script expected.
   That measures the model against the lesson, which is what a training
   record should capture.

4. A MISSING MODEL IS 503, AND THE SESSION IS STILL RECORDED.

   Same shape as Task 56: the user's progress through the scenario is
   not lost because inference was unavailable.

5. SCENARIOS ARE PUBLIC TO ANY AUTHENTICATED USER; SESSIONS ARE NOT.

   The catalogue is reference content -- there is nothing per-user about
   it. Sessions are filtered by the token, like history.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.scenario import Scenario, ScenarioTurn
from app.models.simulation import SimulationSession
from app.models.user import User
from app.schemas.simulation import (
    ScenarioDetail,
    ScenarioSummary,
    ScenarioTurnOut,
    SimulateRequest,
    SimulateResponse,
)
from app.services.classifier import ClassifierUnavailable, classify_prompt

router = APIRouter(prefix="/api", tags=["simulation"])

UNAVAILABLE_DETAIL = (
    "The classification model is not available. Your progress through this "
    "scenario has been saved."
)


@router.get("/scenarios", response_model=list[ScenarioSummary])
def list_scenarios(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Scenario]:
    """The scenario catalogue, for Task 83's picker.

    Retired scenarios are excluded. They are kept rather than deleted so
    the sessions that recorded someone running them stay intact.
    """
    return list(
        db.scalars(
            select(Scenario)
            .where(Scenario.is_active.is_(True))
            .order_by(Scenario.code)
        ).all()
    )


@router.get(
    "/scenarios/{slug}",
    response_model=ScenarioDetail,
    responses={404: {"description": "No such scenario"}},
)
def get_scenario(
    slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Scenario:
    """One scenario with its turns, in order.

    THE RESPONSE OMITS `is_attack` AND `annotation`.

    Those are the answers. Sending them with the script would let the
    page -- or anyone reading the network tab -- reveal the lesson before
    the user has worked through it. They come back one turn at a time
    from /api/simulate-attack instead.
    """
    scenario = db.scalar(
        select(Scenario)
        .where(Scenario.slug == slug, Scenario.is_active.is_(True))
        .options(selectinload(Scenario.turns))
    )
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such scenario."
        )
    return scenario


@router.post(
    "/simulate-attack",
    response_model=SimulateResponse,
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "No such scenario, or no such turn in it"},
        503: {"description": UNAVAILABLE_DETAIL},
    },
)
def simulate_attack(
    payload: SimulateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SimulateResponse:
    """Classify one turn of a scenario and record progress.

    See decision 1: the turn is classified by the model, not looked up
    from its authored label. The label is returned alongside so the user
    can see whether the two agree.
    """
    scenario = db.scalar(
        select(Scenario)
        .where(Scenario.slug == payload.scenarioSlug)
        .options(selectinload(Scenario.turns))
    )
    if scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such scenario."
        )

    turn = next(
        (t for t in scenario.turns if t.position == payload.turnPosition), None
    )
    if turn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario has no turn at position {payload.turnPosition}.",
        )

    # See decision 2 -- one session per run, not per turn.
    session = db.scalar(
        select(SimulationSession).where(
            SimulationSession.user_id == user.user_id,
            SimulationSession.scenario_id == scenario.scenario_id,
            SimulationSession.outcome.is_(None),
        )
    )
    if session is None:
        session = SimulationSession(
            user_id=user.user_id,
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.title,
            difficulty=scenario.difficulty,
            score=0,
        )
        db.add(session)
        db.flush()

    expected_classification = (
        "Safe" if not turn.is_attack else _expected_class(scenario.subtype)
    )

    try:
        result = classify_prompt(turn.content)
    except ClassifierUnavailable:
        # Progress is kept -- see decision 4.
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=UNAVAILABLE_DETAIL,
        ) from None

    agreed = result.label == expected_classification
    if agreed:
        session.score = (session.score or 0) + 1

    is_last = payload.turnPosition >= max(t.position for t in scenario.turns)
    if is_last:
        total = len(scenario.turns)
        # "completed" means they reached the end, not that the model was
        # right every time -- the model's accuracy is its own business,
        # not a pass mark for the learner.
        session.finish("completed", score=session.score)
        remaining = total
    else:
        remaining = max(t.position for t in scenario.turns) - payload.turnPosition

    db.commit()

    return SimulateResponse(
        simulationId=session.simulation_id,
        turnPosition=turn.position,
        role=turn.role,
        origin=turn.origin,
        classification=result.label,
        subtype=result.subtype,
        subtypeReliable=result.subtype_reliable,
        confidenceScore=result.confidence,
        expected=expected_classification,
        agreed=agreed,
        annotation=turn.annotation,
        isLastTurn=is_last,
        turnsRemaining=0 if is_last else remaining,
        score=session.score or 0,
        source="api",
    )


def _expected_class(subtype: str) -> str:
    """The 3-class label a sub-type belongs under.

    Imported rather than duplicated -- SUBTYPE_PARENT is the single
    source, set in Task 44.
    """
    from app.models.subtype import SUBTYPE_PARENT

    parent = SUBTYPE_PARENT.get(subtype)
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Scenario sub-type {subtype!r} has no parent class. The "
                f"taxonomy constants have drifted."
            ),
        )
    return parent
