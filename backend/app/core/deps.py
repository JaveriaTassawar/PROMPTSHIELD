"""Authentication and authorisation dependencies.

Task 54 (`get_current_user`) and Task 55 (`require_roles`). Every protected
endpoint from here on takes one of these.

FIVE DECISIONS:

1. THE USER IS LOADED FROM THE DATABASE, NOT READ FROM THE TOKEN.

   Task 52 noted the trade-off: the token carries `role`, so trusting it
   would save a query per request -- but a role change would then not take
   effect until the token expired. An admin demoted at 10:00 would keep
   admin rights until 11:00.

   This resolves it the safe way. One indexed primary-key lookup per
   request is cheap; a stale privilege is not. The `role` claim stays in
   the token for clients to read, but **the server never trusts it**.

2. A DELETED OR DEACTIVATED USER IS REJECTED EVEN WITH A VALID TOKEN.

   The signature only proves the token was issued by us. It says nothing
   about whether the account still exists or is still enabled. Without
   this check, deactivating an account would do nothing until the token
   expired -- which defeats the point of deactivating it.

3. EVERY FAILURE IS 401 WITH ONE MESSAGE.

   Missing header, malformed token, expired token, unknown user: all
   "not authenticated". Distinguishing them tells an attacker which of
   their forged tokens got furthest.

   The exception is the deactivated account, which is 403 -- the caller
   authenticated successfully and needs to know the problem is not their
   token. That mirrors the login endpoint.

4. require_roles IS A FACTORY, NOT A DEPENDENCY.

   `Depends(require_roles("admin"))` reads at the call site and keeps the
   allowed set next to the endpoint it guards, rather than in a separate
   table of route-to-role mappings that drifts out of date.

5. INSUFFICIENT ROLE IS 403, NOT 404.

   Some APIs hide protected routes behind a 404 so their existence is not
   revealed. Not done here: these routes are documented in the OpenAPI
   schema anyway, so a 404 would mislead a legitimate user without
   concealing anything from an attacker who read /docs.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.tokens import user_id_from_token
from app.models.user import User

# auto_error=False so a missing header reaches our handler and produces the
# same 401 as a bad token. With the default, FastAPI raises a 403 for a
# missing header, which is both the wrong code and a different shape of
# error for what is the same situation.
_bearer = HTTPBearer(auto_error=False)

NOT_AUTHENTICATED_DETAIL = "Not authenticated."
INACTIVE_ACCOUNT_DETAIL = "This account has been deactivated."
FORBIDDEN_DETAIL = "You do not have permission to perform this action."


def _unauthenticated() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=NOT_AUTHENTICATED_DETAIL,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the caller from the Authorization header.

    Raises 401 when the token is missing, malformed, expired or names a
    user who no longer exists; 403 when the account is deactivated.
    """
    if credentials is None or not credentials.credentials:
        raise _unauthenticated()

    user_id = user_id_from_token(credentials.credentials)
    if user_id is None:
        raise _unauthenticated()

    # Loaded fresh -- see decision 1. The token's `role` claim is not
    # consulted.
    user = db.get(User, user_id)
    if user is None:
        # Valid signature, but the account is gone. Same 401: the token
        # is no longer usable and why is not the caller's business.
        raise _unauthenticated()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INACTIVE_ACCOUNT_DETAIL,
        )

    return user


def require_roles(*allowed: str):
    """Build a dependency that admits only the given roles.

        @router.get("/admin/users", dependencies=[Depends(require_roles("admin"))])

    The role is taken from the freshly-loaded user, so a demotion takes
    effect on the next request rather than at token expiry.
    """
    if not allowed:
        raise ValueError("require_roles needs at least one role")

    allowed_set = frozenset(allowed)

    def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=FORBIDDEN_DETAIL,
            )
        return user

    return _dependency


# Convenience for the commonest case. Task 64's admin endpoints use this.
require_admin = require_roles("admin")
