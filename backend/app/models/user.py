"""User model.

Task 41. Backs registration (Task 50), login (Task 51) and the role-gated
dependency in Task 55.

FOUR DECISIONS THAT MATTER, THREE OF THEM SECURITY:

1. THE COLUMN IS `password_hash`, NOT `password`.

   The plan names the field `password`. Naming it that invites
   `User(password=payload.password)` -- which stores plaintext and passes
   every test, because nothing about a string column objects. Renaming it
   makes the mistake visible at the call site: `password_hash=` reads wrong
   when handed a raw password.

   For a project whose subject is security, a plaintext password column
   found by an examiner would undercut the whole thing. 60 chars is bcrypt's
   fixed output width.

2. EMAIL IS CASE-FOLDED BEFORE IT IS STORED.

   `Jawaria@ucp.edu.pk` and `jawaria@ucp.edu.pk` are the same mailbox, but a
   plain UNIQUE index treats them as two accounts. That is a duplicate-
   registration hole and a login that works only with the original casing.
   `normalise_email()` lowercases and strips; Task 50 must call it on both
   register and login.

3. ROLE IS A CHECK-CONSTRAINED STRING, NOT A FREE ONE.

   Task 55 gates endpoints on role. If a typo can write `"admim"`, that user
   silently loses access with no error anywhere. The constraint rejects it at
   the database, which is the only layer every write path goes through.

   A native SQL ENUM would be stricter but needs a migration to add a value,
   and SQLite has no real enum type -- so a CHECK constraint is the portable
   choice here.

4. created_at USES A SERVER DEFAULT, NOT datetime.now().

   A Python default records the application server's clock and timezone. A
   server default records the database's, consistently for every row however
   it was inserted -- including a manual SQL insert or a seed script.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

# Pinned by Task 55. Kept as a module constant so the dependency there and
# the schema here cannot drift apart.
USER_ROLES = ("student", "developer", "researcher", "admin")
DEFAULT_ROLE = "student"

# bcrypt always emits 60 characters.
BCRYPT_HASH_LENGTH = 60


def normalise_email(email: str) -> str:
    """Lowercase and strip, so one mailbox cannot become two accounts.

    Task 50 must call this on registration *and* login -- normalising only
    on write still leaves a user unable to log in with different casing.
    """
    return email.strip().lower()


class User(Base):
    """A registered account."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)

    user_name: Mapped[str] = mapped_column(String(80), nullable=False)

    # Unique and indexed: login looks up by email on every request.
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    # See decision 1. Never assign a raw password to this.
    password_hash: Mapped[str] = mapped_column(
        String(BCRYPT_HASH_LENGTH), nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DEFAULT_ROLE, server_default=DEFAULT_ROLE
    )

    # Lets an admin disable an account without deleting its prompt history,
    # which the analytics in Tasks 60-63 still need.
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True, server_default="1"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),  # see decision 4
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('" + "', '".join(USER_ROLES) + "')",
            name="ck_users_role_valid",
        ),
        Index("ix_users_role", "role"),
    )

    def __repr__(self) -> str:
        # Never render password_hash, even truncated -- repr() lands in logs
        # and tracebacks.
        return (
            f"User(user_id={self.user_id}, email={self.email!r}, "
            f"role={self.role!r})"
        )
