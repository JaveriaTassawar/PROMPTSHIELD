"""Authentication endpoints.

Task 50 (register) and Task 51 (duplicate email handling).

THREE DECISIONS:

1. DUPLICATE EMAIL RETURNS 409, NOT 400.

   Task 51 says pick one and be consistent. 409 Conflict is correct: the
   request was well-formed, and it failed because of existing state rather
   than anything wrong with the input. 400 would be indistinguishable from
   a validation error, and the frontend needs to tell those apart to show
   "that email is taken" instead of "check your details".

   Documented in the OpenAPI responses so Rana can code against it without
   reading this file.

2. THE UNIQUE VIOLATION IS CAUGHT AS WELL AS PRE-CHECKED.

   The pre-check gives a clean error message; the try/except catches the
   race where two requests with the same email pass the check before
   either commits. Without it, the loser gets a 500. This is rare on
   SQLite and entirely real on Postgres under load.

3. ROLE IS ACCEPTED FROM THE REQUEST -- A NOTE FOR TASK 55.

   The frontend's register form posts a role, so it is honoured here,
   which means anyone can currently register as `admin`. That is fine
   while there is no admin functionality, but Task 55 adds role-gated
   endpoints and must close this: either drop role from this endpoint and
   default everyone to `student`, or require an existing admin to grant
   it. Flagged in the plan file too.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.core.tokens import create_access_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api", tags=["auth"])

# Verified against when no user matches, so an unknown email costs the
# same time as a wrong password. Generated once at import; the value is
# irrelevant, only the work of checking it matters.
_TIMING_DUMMY_HASH = hash_password("timing-equalisation-placeholder")

DUPLICATE_EMAIL_DETAIL = "An account with that email already exists."

# One message for every login failure -- see the login docstring.
INVALID_CREDENTIALS_DETAIL = "Incorrect email or password."
INACTIVE_ACCOUNT_DETAIL = "This account has been deactivated."


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"description": DUPLICATE_EMAIL_DETAIL},
        422: {"description": "Validation failed (bad email, short password, unknown role)"},
    },
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Create an account.

    The email is already case-folded by the schema validator, so the
    uniqueness check and the stored value agree.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=DUPLICATE_EMAIL_DETAIL,
        )

    user = User(
        user_name=payload.user_name,
        email=payload.email,
        # The column is named password_hash precisely so that passing a
        # raw password here would read wrong. See Task 41.
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        # Lost the race described in decision 2 -- another request
        # committed the same email between the check above and this
        # commit. Same answer as the pre-check.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=DUPLICATE_EMAIL_DETAIL,
        ) from None

    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"description": INVALID_CREDENTIALS_DETAIL},
        403: {"description": INACTIVE_ACCOUNT_DETAIL},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Verify credentials and return a JWT.

    THE SAME 401 FOR AN UNKNOWN EMAIL AND A WRONG PASSWORD.

    Two different messages would turn this endpoint into an account
    enumerator: an attacker could submit any email and learn from the
    response whether that person has an account. For a security-education
    tool, leaking its own user list would be a poor advertisement.

    The password is also verified even when no user matched. Returning
    early on an unknown email makes that path measurably faster, and the
    difference is enough to enumerate accounts by timing alone. Hashing a
    throwaway value keeps both paths comparable.

    A DEACTIVATED ACCOUNT GETS 403, NOT 401.

    Different situation: the credentials were right. A 401 would send the
    user into a password reset that cannot help them. Task 41 added
    `is_active` for exactly this.
    """
    settings = get_settings()

    user = db.query(User).filter(User.email == payload.email).first()

    if user is None:
        # No account. Verify against a dummy hash anyway so this path
        # costs roughly what the real one does -- see the docstring.
        verify_password(payload.password, _TIMING_DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_DETAIL,
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Checked AFTER the password, so a wrong password on a disabled
    # account still answers 401 -- otherwise the 403 reveals that the
    # account exists.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INACTIVE_ACCOUNT_DETAIL,
        )

    return TokenResponse(
        access_token=create_access_token(user.user_id, user.role),
        expires_in_minutes=settings.jwt_expire_minutes,
        user=UserResponse.model_validate(user),
    )
