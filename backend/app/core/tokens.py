"""JWT creation and decoding.

Task 52. Separate from `security.py` (passwords) so the two concerns can
change independently, and separate from the router so Task 54's
`get_current_user` dependency verifies with the same code that signs.

FOUR DECISIONS:

1. THE SUBJECT IS A STRING, EVEN THOUGH user_id IS AN INT.

   RFC 7519 requires `sub` to be a string. Several libraries reject a
   numeric one, and python-jose will happily sign it but a different
   client library may refuse to read it. Converted on the way in and back
   on the way out, so callers still deal in ints.

2. EXPIRY IS MANDATORY AND COMES FROM SETTINGS.

   A token without `exp` never expires -- a leaked one works forever.
   `JWT_EXPIRE_MINUTES` drives it, defaulting to 60.

3. decode_token() RETURNS None RATHER THAN RAISING.

   Expired, tampered and malformed tokens are all "not authenticated", and
   the caller should not have to distinguish them to produce a 401.
   Returning None keeps that decision in one place and avoids a 500 from
   an unhandled JWTError on a hostile input.

4. THE ROLE IS IN THE TOKEN, BUT IS NOT AUTHORITATIVE FOR LONG.

   Task 55 gates endpoints on role. Carrying it in the token avoids a
   database lookup per request, but it also means a role *change* does not
   take effect until the token expires -- an admin demoted at 10:00 keeps
   admin rights until 11:00.

   That is an accepted trade-off at a 60-minute expiry. If Task 55 needs
   immediate revocation, it must read the role from the database instead of
   trusting this claim.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings

# Claim names. `sub` and `exp` are RFC 7519; `role` is ours.
CLAIM_SUBJECT = "sub"
CLAIM_ROLE = "role"
CLAIM_EXPIRY = "exp"
CLAIM_ISSUED_AT = "iat"


def create_access_token(
    user_id: int,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    """Sign a token carrying the user's id and role."""
    settings = get_settings()
    minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.jwt_expire_minutes
    )

    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        # String, not int -- see decision 1.
        CLAIM_SUBJECT: str(user_id),
        CLAIM_ROLE: role,
        CLAIM_ISSUED_AT: now,
        CLAIM_EXPIRY: now + timedelta(minutes=minutes),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """Return the claims, or None if the token is unusable.

    None covers expired, tampered, malformed and wrong-algorithm tokens --
    all of which mean the same thing to a caller: not authenticated.
    See decision 3.
    """
    if not token:
        return None

    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            # Pinned, so a token claiming alg=none or a weaker algorithm
            # is rejected rather than trusted.
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None

    # A token with no subject is structurally valid but useless, and
    # treating it as authenticated would be worse than rejecting it.
    if not claims.get(CLAIM_SUBJECT):
        return None

    return claims


def user_id_from_token(token: str) -> int | None:
    """The user id, or None. Converts `sub` back to an int."""
    claims = decode_token(token)
    if claims is None:
        return None
    try:
        return int(claims[CLAIM_SUBJECT])
    except (ValueError, TypeError, KeyError):
        return None
