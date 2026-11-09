"""Tests for Task 50 (register) and Task 51 (duplicate email).

The security tests are the point of this file:

  - the response must never carry password_hash
  - the stored value must never equal the submitted password
  - two casings of one email must not become two accounts
  - a password past bcrypt's 72-byte limit must be rejected, not truncated

The last one is subtle. bcrypt silently ignores bytes past 72, so two long
passwords sharing a prefix would unlock each other's accounts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import MAX_PASSWORD_BYTES, verify_password
from app.models.user import User

VALID = {
    "name": "Jawaria Tassawar",
    "email": "jawaria@ucp.edu.pk",
    "password": "a-strong-password",
    "role": "student",
}


def test_register_returns_201(client: TestClient) -> None:
    response = client.post("/api/register", json=VALID)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jawaria@ucp.edu.pk"
    assert body["user_name"] == "Jawaria Tassawar"
    assert body["role"] == "student"
    assert body["is_active"] is True
    assert body["user_id"] > 0


def test_response_never_contains_the_hash(client: TestClient) -> None:
    """UserResponse lists fields explicitly so a column added later
    cannot leak through this endpoint."""
    body = client.post("/api/register", json=VALID).json()

    assert "password_hash" not in body
    assert "password" not in body


def test_password_is_hashed_not_stored(
    client: TestClient, db_session: Session
) -> None:
    client.post("/api/register", json=VALID)

    user = db_session.query(User).one()
    assert user.password_hash != VALID["password"]
    assert user.password_hash.startswith("$2")  # bcrypt marker
    assert verify_password(VALID["password"], user.password_hash)


def test_wrong_password_does_not_verify(
    client: TestClient, db_session: Session
) -> None:
    client.post("/api/register", json=VALID)

    user = db_session.query(User).one()
    assert not verify_password("not-the-password", user.password_hash)


def test_duplicate_email_returns_409(client: TestClient) -> None:
    """Task 51. 409 rather than 400, so the frontend can distinguish
    'that email is taken' from 'check your details'."""
    assert client.post("/api/register", json=VALID).status_code == 201

    second = client.post("/api/register", json=VALID)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"]


def test_duplicate_email_is_case_insensitive(client: TestClient) -> None:
    """Otherwise one mailbox becomes two accounts, and the user cannot
    log in unless they match their original capitalisation."""
    client.post("/api/register", json=VALID)

    shouted = dict(VALID, email="JAWARIA@UCP.EDU.PK")
    assert client.post("/api/register", json=shouted).status_code == 409


def test_email_is_stored_lowercase(
    client: TestClient, db_session: Session
) -> None:
    client.post("/api/register", json=dict(VALID, email="Jawaria@UCP.edu.PK"))

    assert db_session.query(User).one().email == "jawaria@ucp.edu.pk"


def test_oversized_password_is_rejected_not_truncated(
    client: TestClient,
) -> None:
    """bcrypt ignores bytes past 72, so two long passwords sharing a
    prefix would unlock each other. Rejected with 422 instead."""
    response = client.post(
        "/api/register", json=dict(VALID, password="x" * (MAX_PASSWORD_BYTES + 1))
    )

    assert response.status_code == 422
    assert "72" in str(response.json())


def test_password_at_the_limit_is_accepted(client: TestClient) -> None:
    response = client.post(
        "/api/register", json=dict(VALID, password="x" * MAX_PASSWORD_BYTES)
    )
    assert response.status_code == 201


def test_short_password_is_rejected(client: TestClient) -> None:
    response = client.post("/api/register", json=dict(VALID, password="short"))
    assert response.status_code == 422


def test_invalid_email_is_rejected(client: TestClient) -> None:
    response = client.post("/api/register", json=dict(VALID, email="not-an-email"))
    assert response.status_code == 422


def test_unknown_role_is_rejected_with_422(client: TestClient) -> None:
    """422 naming the valid roles, rather than a 500 from the database
    CHECK constraint."""
    response = client.post("/api/register", json=dict(VALID, role="superuser"))

    assert response.status_code == 422
    assert "student" in str(response.json())


def test_role_defaults_to_student(client: TestClient) -> None:
    payload = {k: v for k, v in VALID.items() if k != "role"}
    body = client.post("/api/register", json=payload).json()

    assert body["role"] == "student"


def test_blank_name_is_rejected(client: TestClient) -> None:
    response = client.post("/api/register", json=dict(VALID, name="   "))
    assert response.status_code == 422


def test_name_is_stripped(client: TestClient) -> None:
    body = client.post("/api/register", json=dict(VALID, name="  Jawaria  ")).json()
    assert body["user_name"] == "Jawaria"


def test_two_different_emails_both_register(client: TestClient) -> None:
    assert client.post("/api/register", json=VALID).status_code == 201
    other = dict(VALID, email="faiqa@ucp.edu.pk")
    assert client.post("/api/register", json=other).status_code == 201


def test_endpoint_appears_in_openapi(client: TestClient) -> None:
    """So Rana can code against it from /docs without reading the source."""
    schema = client.get("/openapi.json").json()

    assert "/api/register" in schema["paths"]
    responses = schema["paths"]["/api/register"]["post"]["responses"]
    assert "201" in responses
    assert "409" in responses, "the duplicate-email status must be documented"


# --- privilege escalation fix ---------------------------------------------


def test_cannot_self_register_as_admin(client: TestClient) -> None:
    """The endpoint is unauthenticated, so honouring a posted role of
    `admin` would let any visitor grant themselves administrator rights.

    frontend/src/pages/RegisterPage.jsx already omits admin from its
    options; this is the server-side enforcement, because a form is not
    a security control.
    """
    response = client.post("/api/register", json=dict(VALID, role="admin"))

    assert response.status_code == 422
    assert "admin" not in response.json()["detail"][0]["msg"]


def test_admin_cannot_be_created_through_the_api(
    client: TestClient, db_session: Session
) -> None:
    """Belt and braces: no admin row exists after the attempt."""
    client.post("/api/register", json=dict(VALID, role="admin"))

    assert db_session.query(User).filter(User.role == "admin").count() == 0


def test_organization_role_is_accepted(client: TestClient) -> None:
    """The frontend offers Organization; before this it returned 422
    from a CHECK constraint the Python constant had drifted from."""
    response = client.post("/api/register", json=dict(VALID, role="organization"))

    assert response.status_code == 201
    assert response.json()["role"] == "organization"


def test_every_frontend_role_option_is_accepted(client: TestClient) -> None:
    """The four values in RegisterPage.jsx ROLES must all work."""
    for index, role in enumerate(
        ("student", "developer", "researcher", "organization")
    ):
        payload = dict(VALID, role=role, email=f"user{index}@ucp.edu.pk")
        response = client.post("/api/register", json=payload)
        assert response.status_code == 201, f"{role} was rejected"
