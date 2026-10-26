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

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest, UserResponse

router = APIRouter(prefix="/api", tags=["auth"])

DUPLICATE_EMAIL_DETAIL = "An account with that email already exists."


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
