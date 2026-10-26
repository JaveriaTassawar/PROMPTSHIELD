"""Password hashing.

Task 50. Isolated from the endpoint so Task 52's login verifies against the
same implementation, and so a future algorithm change happens in one place.

THREE DECISIONS:

1. THE `bcrypt` PACKAGE DIRECTLY, NOT `passlib`.

   The plan named passlib. It was tried first and does not work here:
   passlib 1.7.4 reads `bcrypt.__about__.__version__`, which bcrypt 5.0
   removed, so every hash call raises before producing anything. passlib's
   last release was 2020.

   Using bcrypt directly removes an unmaintained dependency from the auth
   path and costs about ten lines. The stored format is identical -- a
   standard `$2b$` hash -- so nothing downstream changes, and passlib could
   be reintroduced later without a migration.

2. BCRYPT'S 72-BYTE LIMIT IS REJECTED, NOT TRUNCATED.

   bcrypt ignores input past 72 *bytes*. Two different long passwords
   sharing their first 72 bytes hash identically, so each would unlock the
   other's account. bcrypt 5.0 raises on over-long input rather than
   truncating, but this module checks explicitly so the error is the same
   regardless of version, and so the message says why.

   Bytes, not characters: a non-ASCII password reaches the limit sooner
   than its length suggests.

3. verify_password() NEVER RAISES.

   A corrupted or legacy value in the column returns False rather than a
   500. A failed login is the right outcome either way, and an exception
   would leak the difference between "wrong password" and "something is
   odd about this account" to anyone probing the endpoint.
"""

from __future__ import annotations

import bcrypt

# bcrypt ignores input past this -- see decision 2.
MAX_PASSWORD_BYTES = 72

# A floor, not a strength policy; Task 53 owns validation rules.
MIN_PASSWORD_LENGTH = 8

# Work factor. 12 is the common default: roughly 0.3s per hash, slow
# enough to make offline cracking expensive, fast enough for a login.
BCRYPT_ROUNDS = 12


class PasswordTooLongError(ValueError):
    """Raised rather than letting the first 72 bytes stand in for the rest."""


def hash_password(password: str) -> str:
    """Return a bcrypt hash, or raise if the input cannot be hashed safely."""
    if not password:
        raise ValueError("password must not be empty")

    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(
            f"password is {len(encoded)} bytes; bcrypt ignores anything past "
            f"{MAX_PASSWORD_BYTES}, so it is rejected rather than stored as "
            f"something other than what was typed"
        )

    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """True if the password matches. Never raises -- see decision 3."""
    if not password or not password_hash:
        return False

    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        # Cannot match anything hash_password() produced, and bcrypt 5
        # would raise. Answer False rather than error.
        return False

    try:
        return bcrypt.checkpw(encoded, password_hash.encode())
    except (ValueError, TypeError):
        # Malformed or legacy hash.
        return False
