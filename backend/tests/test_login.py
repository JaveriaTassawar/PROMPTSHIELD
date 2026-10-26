"""Tests for Task 52 (login + JWT).

The security tests here are about what the endpoint *does not* reveal:

  - the same 401 for an unknown email and a wrong password, so the
    endpoint cannot be used to enumerate who has an account
  - no password or hash anywhere in the response
  - a tampered or expired token is rejected, not merely frowned at
"""

from __future__ import annotations

import time

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.tokens import (
    CLAIM_EXPIRY,
    CLAIM_ROLE,
    CLAIM_SUBJECT,
    create_access_token,
    decode_token,
    user_id_from_token,
)
from app.models.user import User

ACCOUNT = {
    "name": "Jawaria Tassawar",
    "email": "jawaria@ucp.edu.pk",
    "password": "a-strong-password",
    "role": "student",
}
CREDENTIALS = {"email": ACCOUNT["email"], "password": ACCOUNT["password"]}


def register(client: TestClient, **overrides) -> dict:
    payload = dict(ACCOUNT, **overrides)
    response = client.post("/api/register", json=payload)
    assert response.status_code == 201
    return response.json()


def test_login_returns_a_token(client: TestClient) -> None:
    register(client)

    response = client.post("/api/login", json=CREDENTIALS)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in_minutes"] > 0


def test_token_carries_user_id_and_role(client: TestClient) -> None:
    """Task 52 requires both claims."""
    created = register(client)

    token = client.post("/api/login", json=CREDENTIALS).json()["access_token"]
    claims = decode_token(token)

    assert claims is not None
    assert claims[CLAIM_SUBJECT] == str(created["user_id"])
    assert claims[CLAIM_ROLE] == "student"
    assert CLAIM_EXPIRY in claims, "a token without exp never expires"


def test_subject_is_a_string_but_reads_back_as_int(
    client: TestClient,
) -> None:
    """RFC 7519 requires `sub` to be a string; callers want an int."""
    created = register(client)
    token = client.post("/api/login", json=CREDENTIALS).json()["access_token"]

    assert isinstance(decode_token(token)[CLAIM_SUBJECT], str)
    assert user_id_from_token(token) == created["user_id"]


def test_response_includes_the_user_but_not_the_hash(
    client: TestClient,
) -> None:
    register(client)

    body = client.post("/api/login", json=CREDENTIALS).json()

    assert body["user"]["email"] == ACCOUNT["email"]
    assert "password_hash" not in body["user"]
    assert "password" not in str(body)


def test_wrong_password_is_401(client: TestClient) -> None:
    register(client)

    response = client.post(
        "/api/login", json={"email": ACCOUNT["email"], "password": "wrong"}
    )

    assert response.status_code == 401


def test_unknown_email_is_401_with_the_same_message(
    client: TestClient,
) -> None:
    """Different messages would turn this endpoint into an account
    enumerator -- submit any email, learn whether it has an account."""
    register(client)

    wrong_password = client.post(
        "/api/login", json={"email": ACCOUNT["email"], "password": "wrong"}
    )
    unknown_email = client.post(
        "/api/login", json={"email": "nobody@ucp.edu.pk", "password": "wrong"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_login_is_case_insensitive(client: TestClient) -> None:
    """Task 41 flagged this: normalising only on registration leaves
    the user unable to log in with different casing."""
    register(client, email="Jawaria@UCP.edu.pk")

    response = client.post(
        "/api/login",
        json={"email": "JAWARIA@ucp.EDU.pk", "password": ACCOUNT["password"]},
    )

    assert response.status_code == 200


def test_deactivated_account_is_403_not_401(
    client: TestClient, db_session: Session
) -> None:
    """The credentials were right, so 401 would send the user into a
    password reset that cannot help them."""
    register(client)
    user = db_session.query(User).one()
    user.is_active = False
    db_session.commit()

    response = client.post("/api/login", json=CREDENTIALS)

    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"]


def test_deactivated_account_with_wrong_password_is_still_401(
    client: TestClient, db_session: Session
) -> None:
    """Otherwise the 403 reveals that the account exists."""
    register(client)
    user = db_session.query(User).one()
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/login", json={"email": ACCOUNT["email"], "password": "wrong"}
    )

    assert response.status_code == 401


def test_www_authenticate_header_on_401(client: TestClient) -> None:
    register(client)

    response = client.post(
        "/api/login", json={"email": ACCOUNT["email"], "password": "wrong"}
    )

    assert response.headers.get("www-authenticate") == "Bearer"


# --- token handling --------------------------------------------------------


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(1, "student")
    head, payload, signature = token.split(".")
    forged = f"{head}.{payload}.{'x' * len(signature)}"

    assert decode_token(forged) is None


def test_token_with_swapped_payload_is_rejected() -> None:
    """Escalating `role` in the payload must invalidate the signature."""
    import base64
    import json

    token = create_access_token(1, "student")
    head, payload, signature = token.split(".")

    raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    claims = json.loads(raw)
    claims[CLAIM_ROLE] = "admin"
    forged_payload = (
        base64.urlsafe_b64encode(json.dumps(claims).encode())
        .decode()
        .rstrip("=")
    )

    assert decode_token(f"{head}.{forged_payload}.{signature}") is None


def test_expired_token_is_rejected() -> None:
    """Negative expiry puts it in the past."""
    token = create_access_token(1, "student", expires_minutes=-1)
    time.sleep(0.01)

    assert decode_token(token) is None


def test_garbage_token_returns_none_rather_than_raising() -> None:
    """A hostile input must not produce a 500."""
    for junk in ("", "not-a-token", "a.b.c", "....", "x" * 500):
        assert decode_token(junk) is None
        assert user_id_from_token(junk) is None


def test_login_endpoint_is_documented(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/api/login" in schema["paths"]
    responses = schema["paths"]["/api/login"]["post"]["responses"]
    assert "401" in responses
    assert "403" in responses
