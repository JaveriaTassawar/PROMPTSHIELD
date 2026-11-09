"""Request and response bodies for the Simulation Lab.

Task 63. Field names follow the frontend's existing mock shapes in
`frontend/src/mocks/simulation.js`, so Tasks 83-85 can switch source
without reshaping the pages.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ScenarioSummary(BaseModel):
    """A catalogue entry, for Task 83's picker.

    `slug` is the identifier the UI routes on -- /simulation/:scenarioId --
    because a readable slug survives a reseed where an autoincrement id
    does not.
    """

    slug: str
    code: str
    title: str
    subtype: str
    difficulty: str
    summary: str
    objective: str

    model_config = ConfigDict(from_attributes=True)


class ScenarioTurnOut(BaseModel):
    """One turn, as sent to the page.

    DELIBERATELY OMITS `is_attack` AND `annotation`.

    Those are the answers. Including them in the script would let the
    page -- or anyone reading the network tab -- reveal the lesson before
    the user has worked through it. They arrive one turn at a time from
    /api/simulate-attack.
    """

    position: int
    role: str
    # 'dataset' or 'authored'. A learner shown a real attack and a
    # written one should be able to tell which is which.
    origin: str
    content: str

    model_config = ConfigDict(from_attributes=True)


class ScenarioDetail(ScenarioSummary):
    """A scenario with its turns, in order."""

    turns: list[ScenarioTurnOut] = Field(default_factory=list)


class SimulateRequest(BaseModel):
    """Body of POST /api/simulate-attack.

    Identifies a turn rather than carrying its text. The server has the
    script, so accepting arbitrary text here would let a caller claim
    any string was "turn 2 of SIM-03" and record a session against it.
    """

    scenarioSlug: str
    turnPosition: int = Field(ge=1)


class SimulateResponse(BaseModel):
    """The model's verdict on one turn, plus the script's own label.

    `classification` is what the real classifier said. `expected` is what
    the scenario author labelled it. `agreed` is whether they matched --
    and a learner seeing them differ is learning something true about
    the model rather than watching a scripted result.
    """

    simulationId: int
    turnPosition: int
    role: str
    origin: str

    classification: str
    subtype: str | None = None
    subtypeReliable: bool = True
    confidenceScore: float

    expected: str
    agreed: bool

    # The scenario's teaching note, released only now that the turn has
    # been scanned.
    annotation: str | None = None

    isLastTurn: bool
    turnsRemaining: int
    score: int

    # 'api' here; the frontend mock reports 'annotation'. Lets the UI show
    # whether a detection came from the model or from seeded content, and
    # lets Task 85 tell them apart while both exist.
    source: str = "api"
