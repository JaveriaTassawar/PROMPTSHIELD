"""Tests for Task 63 (the Simulation Lab endpoints).

The three that carry weight:

  - the turn is classified by the MODEL, not read from its authored
    `is_attack` label. Returning the label would make the lab a
    slideshow showing perfect accuracy even with a broken model.

  - the script response must not leak `is_attack` or `annotation`.
    Those are the answers, and anyone reading the network tab would see
    the lesson before working through it.

  - one session per run, not per turn. Written per turn, a three-turn
    scenario would triple the Tasks 60-63 completion counts.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.simulation import SimulationSession
from app.seed.scenarios import seed_scenarios
from app.services.classifier import ClassificationResult, ClassifierUnavailable

ACCOUNT = {
    "name": "Jawaria",
    "email": "jawaria@ucp.edu.pk",
    "password": "a-strong-password",
}


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def token(client: TestClient, db_session: Session) -> str:
    seed_scenarios(db_session)
    client.post("/api/register", json=ACCOUNT)
    return client.post(
        "/api/login",
        json={"email": ACCOUNT["email"], "password": ACCOUNT["password"]},
    ).json()["access_token"]


@pytest.fixture
def stub_jailbreak(monkeypatch) -> None:
    """The model always says Direct Jailbreak.

    Deliberately wrong for the harmless turns, so the tests can tell a
    real classification from a lookup of `is_attack`.
    """
    monkeypatch.setattr(
        "app.routers.simulation.classify_prompt",
        lambda text: ClassificationResult(
            label="Direct Jailbreak",
            confidence=0.91,
            subtype="Persona Hijacking",
        ),
    )


# --- the catalogue ---------------------------------------------------------


def test_catalogue_lists_the_seeded_scenarios(
    client: TestClient, token: str
) -> None:
    response = client.get("/api/scenarios", headers=auth(token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    assert {s["code"] for s in body} >= {"SIM-01", "SIM-02"}


def test_catalogue_is_ordered_by_code(client: TestClient, token: str) -> None:
    codes = [s["code"] for s in client.get("/api/scenarios", headers=auth(token)).json()]
    assert codes == sorted(codes)


def test_catalogue_requires_auth(client: TestClient) -> None:
    assert client.get("/api/scenarios").status_code == 401


def test_retired_scenario_is_hidden(
    client: TestClient, token: str, db_session: Session
) -> None:
    """Retired rather than deleted, so the sessions that ran it survive."""
    from app.models.scenario import Scenario

    scenario = db_session.query(Scenario).filter_by(slug="unrestricted-persona").one()
    scenario.is_active = False
    db_session.commit()

    slugs = {s["slug"] for s in client.get("/api/scenarios", headers=auth(token)).json()}
    assert "unrestricted-persona" not in slugs


# --- the script ------------------------------------------------------------


def test_script_returns_turns_in_order(client: TestClient, token: str) -> None:
    body = client.get(
        "/api/scenarios/gradual-escalation", headers=auth(token)
    ).json()

    positions = [t["position"] for t in body["turns"]]
    assert positions == sorted(positions)
    assert len(positions) >= 3


def test_script_does_not_leak_the_answers(
    client: TestClient, token: str
) -> None:
    """is_attack and annotation are the lesson. Sending them with the
    script would reveal it before the user has worked through it --
    visible to anyone reading the network tab."""
    body = client.get(
        "/api/scenarios/gradual-escalation", headers=auth(token)
    ).json()

    for turn in body["turns"]:
        assert "is_attack" not in turn
        assert "isAttack" not in turn
        assert "annotation" not in turn


def test_script_carries_provenance(client: TestClient, token: str) -> None:
    """A learner shown a real attack and a written one should be able to
    tell which is which."""
    body = client.get(
        "/api/scenarios/poisoned-document", headers=auth(token)
    ).json()

    for turn in body["turns"]:
        assert turn["origin"] in ("dataset", "authored")


def test_unknown_scenario_is_404(client: TestClient, token: str) -> None:
    response = client.get("/api/scenarios/no-such-thing", headers=auth(token))
    assert response.status_code == 404


# --- scanning a turn -------------------------------------------------------


def test_turn_is_classified_by_the_model_not_the_label(
    client: TestClient, token: str, stub_jailbreak
) -> None:
    """THE test for this task.

    Turn 1 of gradual-escalation is authored as harmless. The stub says
    Direct Jailbreak. If the endpoint returned the authored label we
    would see "Safe" here -- so seeing the stub's answer proves the
    model is actually being called.
    """
    body = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "gradual-escalation", "turnPosition": 1},
        headers=auth(token),
    ).json()

    assert body["classification"] == "Direct Jailbreak"  # the model
    assert body["expected"] == "Safe"                    # the script
    assert body["agreed"] is False
    assert body["source"] == "api"


def test_agreement_is_reported_when_they_match(
    client: TestClient, token: str, stub_jailbreak
) -> None:
    """Turn 1 of SIM-01 IS authored as an attack, so the stub agrees."""
    body = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(token),
    ).json()

    assert body["expected"] == "Direct Jailbreak"
    assert body["agreed"] is True


def test_annotation_is_released_only_after_scanning(
    client: TestClient, token: str, stub_jailbreak
) -> None:
    body = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(token),
    ).json()

    assert body["annotation"]


def test_request_identifies_a_turn_rather_than_carrying_text() -> None:
    """Accepting arbitrary text would let a caller claim any string was
    "turn 2 of SIM-03" and record a session against it."""
    from app.schemas.simulation import SimulateRequest

    assert "content" not in SimulateRequest.model_fields
    assert "prompt" not in SimulateRequest.model_fields


def test_unknown_turn_position_is_404(
    client: TestClient, token: str, stub_jailbreak
) -> None:
    response = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 99},
        headers=auth(token),
    )
    assert response.status_code == 404


def test_unauthenticated_is_401(client: TestClient) -> None:
    response = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
    )
    assert response.status_code == 401


# --- session handling ------------------------------------------------------


def test_one_session_per_run_not_per_turn(
    client: TestClient, token: str, stub_jailbreak, db_session: Session
) -> None:
    """Written per turn, a three-turn scenario would triple the Tasks
    60-63 completion counts."""
    for position in (1, 2, 3):
        client.post(
            "/api/simulate-attack",
            json={"scenarioSlug": "gradual-escalation", "turnPosition": position},
            headers=auth(token),
        )

    assert db_session.query(SimulationSession).count() == 1


def test_session_closes_on_the_last_turn(
    client: TestClient, token: str, stub_jailbreak, db_session: Session
) -> None:
    for position in (1, 2, 3):
        body = client.post(
            "/api/simulate-attack",
            json={"scenarioSlug": "gradual-escalation", "turnPosition": position},
            headers=auth(token),
        ).json()

    assert body["isLastTurn"] is True
    assert body["turnsRemaining"] == 0

    session = db_session.query(SimulationSession).one()
    assert session.outcome == "completed"
    assert session.end_time is not None


def test_session_stays_open_mid_scenario(
    client: TestClient, token: str, stub_jailbreak, db_session: Session
) -> None:
    body = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "gradual-escalation", "turnPosition": 1},
        headers=auth(token),
    ).json()

    assert body["isLastTurn"] is False
    assert body["turnsRemaining"] > 0

    session = db_session.query(SimulationSession).one()
    assert session.is_in_progress is True


def test_score_counts_agreements(
    client: TestClient, token: str, stub_jailbreak, db_session: Session
) -> None:
    """The stub always says Direct Jailbreak, and only the last turn of
    gradual-escalation is authored as an attack -- so exactly one
    agreement across three turns."""
    for position in (1, 2, 3):
        client.post(
            "/api/simulate-attack",
            json={"scenarioSlug": "gradual-escalation", "turnPosition": position},
            headers=auth(token),
        )

    assert db_session.query(SimulationSession).one().score == 1


def test_a_second_run_starts_a_new_session(
    client: TestClient, token: str, stub_jailbreak, db_session: Session
) -> None:
    """The first is closed, so the next scan must not reopen it."""
    client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(token),
    )
    client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(token),
    )

    assert db_session.query(SimulationSession).count() == 2


def test_progress_survives_an_unavailable_model(
    client: TestClient, token: str, monkeypatch, db_session: Session
) -> None:
    """Same shape as Task 56: the user's progress is not lost because
    inference was unavailable."""
    def _unavailable(text):
        raise ClassifierUnavailable("no model in this test")

    monkeypatch.setattr("app.routers.simulation.classify_prompt", _unavailable)

    response = client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(token),
    )

    assert response.status_code == 503
    assert db_session.query(SimulationSession).count() == 1


def test_sessions_are_per_user(
    client: TestClient, token: str, stub_jailbreak, db_session: Session
) -> None:
    client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(token),
    )

    other = dict(ACCOUNT, email="faiqa@ucp.edu.pk")
    client.post("/api/register", json=other)
    other_token = client.post(
        "/api/login",
        json={"email": other["email"], "password": other["password"]},
    ).json()["access_token"]
    client.post(
        "/api/simulate-attack",
        json={"scenarioSlug": "unrestricted-persona", "turnPosition": 1},
        headers=auth(other_token),
    )

    sessions = db_session.query(SimulationSession).all()
    assert len({s.user_id for s in sessions}) == 2


def test_endpoints_are_documented(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/scenarios" in paths
    assert "/api/simulate-attack" in paths
    assert "503" in paths["/api/simulate-attack"]["post"]["responses"]
