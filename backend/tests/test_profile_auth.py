"""Tests for Task 54 (JWT-protected profile) and Task 55 (role dependency).

Three tests here cover things that are easy to get wrong and silent when
they are:

  - a demoted user must lose access on the NEXT request, not at token
    expiry, which means the role cannot be read from the token
  - a deactivated user's existing token must stop working immediately,
    or deactivation does nothing for an hour
  - one user's token must never return another user's profile
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_admin, require_roles
from app.core.tokens import create_access_token
from app.models.user import User

ACCOUNT = {
    "name": "Jawaria Tassawar",
    "email": "jawaria@ucp.edu.pk",
    "password": "a-strong-password",
    "role": "student",
}


def register_and_login(client: TestClient, **overrides) -> tuple[dict, str]:
    """Create an account and return (user, token)."""
    payload = dict(ACCOUNT, **overrides)
    created = client.post("/api/register", json=payload).json()
    token = client.post(
        "/api/login",
        json={"email": payload["email"], "password": payload["password"]},
    ).json()["access_token"]
    return created, token


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Task 54: the protected endpoint ---------------------------------------


def test_profile_returns_the_caller(client: TestClient) -> None:
    created, token = register_and_login(client)

    response = client.get("/api/profile", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["user_id"] == created["user_id"]
    assert response.json()["email"] == ACCOUNT["email"]


def test_profile_never_includes_the_hash(client: TestClient) -> None:
    _, token = register_and_login(client)

    body = client.get("/api/profile", headers=auth(token)).json()

    assert "password_hash" not in body
    assert "password" not in body


def test_no_token_is_401(client: TestClient) -> None:
    """Not 403. FastAPI's HTTPBearer defaults to 403 for a missing
    header, which is the wrong code for 'you did not authenticate'."""
    response = client.get("/api/profile")

    assert response.status_code == 401
    assert response.headers.get("www-authenticate") == "Bearer"


def test_garbage_token_is_401(client: TestClient) -> None:
    for junk in ("not-a-token", "a.b.c", "x" * 400):
        assert client.get("/api/profile", headers=auth(junk)).status_code == 401


def test_expired_token_is_401(client: TestClient) -> None:
    created, _ = register_and_login(client)
    stale = create_access_token(created["user_id"], "student", expires_minutes=-1)

    assert client.get("/api/profile", headers=auth(stale)).status_code == 401


def test_token_for_a_deleted_user_is_401(
    client: TestClient, db_session: Session
) -> None:
    """A valid signature only proves we issued it, not that the account
    still exists."""
    _, token = register_and_login(client)
    db_session.delete(db_session.query(User).one())
    db_session.commit()

    assert client.get("/api/profile", headers=auth(token)).status_code == 401


def test_deactivation_takes_effect_immediately(
    client: TestClient, db_session: Session
) -> None:
    """The existing token must stop working at once.

    If the user were read from the token rather than the database,
    deactivating an account would do nothing until it expired -- which
    defeats the point of deactivating it.
    """
    _, token = register_and_login(client)
    assert client.get("/api/profile", headers=auth(token)).status_code == 200

    db_session.query(User).one().is_active = False
    db_session.commit()

    response = client.get("/api/profile", headers=auth(token))
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"]


def test_one_users_token_cannot_read_another_profile(
    client: TestClient,
) -> None:
    """The endpoint takes no user_id, so this is unexpressible -- but
    assert it, because adding such a parameter later would be the
    natural way to introduce the bug."""
    first, first_token = register_and_login(client)
    second, _ = register_and_login(client, email="faiqa@ucp.edu.pk")

    body = client.get("/api/profile", headers=auth(first_token)).json()

    assert body["user_id"] == first["user_id"]
    assert body["user_id"] != second["user_id"]


# --- Task 55: the role dependency ------------------------------------------


@pytest.fixture
def role_app(client: TestClient) -> TestClient:
    """Mount throwaway role-guarded routes on the same app.

    Task 64's admin endpoints do not exist yet, so the dependency is
    exercised directly rather than through a route that is not written.
    """
    app: FastAPI = client.app

    @app.get("/test/admin-only")
    def admin_only(user: User = Depends(require_admin)) -> dict:
        return {"ok": True, "role": user.role}

    @app.get("/test/staff-only")
    def staff_only(
        user: User = Depends(require_roles("researcher", "admin"))
    ) -> dict:
        return {"ok": True, "role": user.role}

    return client


def test_role_dependency_admits_the_right_role(
    role_app: TestClient, db_session: Session
) -> None:
    _, token = register_and_login(role_app, role="researcher")

    response = role_app.get("/test/staff-only", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["role"] == "researcher"


def test_role_dependency_rejects_the_wrong_role(
    role_app: TestClient,
) -> None:
    _, token = register_and_login(role_app, role="student")

    response = role_app.get("/test/staff-only", headers=auth(token))

    assert response.status_code == 403


def test_admin_route_rejects_a_student(role_app: TestClient) -> None:
    _, token = register_and_login(role_app, role="student")

    assert role_app.get("/test/admin-only", headers=auth(token)).status_code == 403


def test_admin_route_admits_an_admin(
    role_app: TestClient, db_session: Session
) -> None:
    """Admin cannot be self-assigned at registration (Task 50 fix), so
    the role is granted directly -- which is what Task 64 will do."""
    _, token = register_and_login(role_app)
    db_session.query(User).one().role = "admin"
    db_session.commit()

    response = role_app.get("/test/admin-only", headers=auth(token))

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_demotion_takes_effect_on_the_next_request(
    role_app: TestClient, db_session: Session
) -> None:
    """THE reason the role is not read from the token.

    Task 52 carries `role` in the JWT so clients can read it. If the
    server trusted that claim, an admin demoted at 10:00 would keep
    admin rights until the token expired at 11:00.
    """
    _, token = register_and_login(role_app)
    user = db_session.query(User).one()
    user.role = "admin"
    db_session.commit()
    assert role_app.get("/test/admin-only", headers=auth(token)).status_code == 200

    # Same token, role revoked.
    user.role = "student"
    db_session.commit()

    assert role_app.get("/test/admin-only", headers=auth(token)).status_code == 403


def test_a_forged_admin_claim_does_not_grant_access(
    role_app: TestClient, db_session: Session
) -> None:
    """Even a correctly-signed token claiming admin is not trusted --
    the role comes from the database."""
    created, _ = register_and_login(role_app, role="student")
    # Signed by us, so the signature is valid; the claim is simply wrong.
    lying_token = create_access_token(created["user_id"], "admin")

    response = role_app.get("/test/admin-only", headers=auth(lying_token))

    assert response.status_code == 403


def test_require_roles_rejects_an_empty_list() -> None:
    """A guard that admits nobody is a mistake, not a lockdown."""
    with pytest.raises(ValueError, match="at least one role"):
        require_roles()


def test_profile_is_documented(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/api/profile" in schema["paths"]
    assert "401" in schema["paths"]["/api/profile"]["get"]["responses"]
