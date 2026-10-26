"""Request and response bodies for authentication.

Task 50. The response model is the security-relevant half of this file.

THE RESPONSE NEVER CONTAINS THE PASSWORD HASH.

`UserResponse` lists its fields explicitly rather than serialising the ORM
object wholesale. If it did the latter, adding any sensitive column to the
User model later would leak it through this endpoint with no code change
and nothing failing. A test asserts `password_hash` is absent.

FIELD NAMES MATCH THE FRONTEND FORM.

`frontend/src/pages/RegisterPage.jsx` posts `name`, `email`, `password` and
`role`. The model stores `user_name`, so `name` is aliased rather than
renamed on either side -- the frontend keeps its form field, the database
keeps its column, and neither has to change.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import MAX_PASSWORD_BYTES, MIN_PASSWORD_LENGTH
from app.models.user import DEFAULT_ROLE, USER_ROLES, normalise_email


class RegisterRequest(BaseModel):
    """Body of POST /api/register."""

    # Aliased: the frontend form field is `name`.
    user_name: str = Field(
        alias="name", min_length=1, max_length=80,
        description="Display name",
    )
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)
    role: str = Field(default=DEFAULT_ROLE)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("email")
    @classmethod
    def _normalise_email(cls, value: str) -> str:
        """Case-fold here so the uniqueness check and the stored value
        agree. Task 52's login must call the same function."""
        return normalise_email(value)

    @field_validator("password")
    @classmethod
    def _password_fits_bcrypt(cls, value: str) -> str:
        """Reject before hashing rather than let bcrypt truncate.

        Returns 422 from the API instead of a 500 from the hasher, and
        the user learns the real reason.
        """
        encoded = value.encode("utf-8")
        if len(encoded) > MAX_PASSWORD_BYTES:
            raise ValueError(
                f"password must be at most {MAX_PASSWORD_BYTES} bytes "
                f"(this one is {len(encoded)})"
            )
        return value

    @field_validator("role")
    @classmethod
    def _known_role(cls, value: str) -> str:
        """Checked here as well as by the database CHECK, so a bad role
        is a 422 naming the valid values rather than a 500."""
        if value not in USER_ROLES:
            raise ValueError(f"role must be one of {', '.join(USER_ROLES)}")
        return value

    @field_validator("user_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class UserResponse(BaseModel):
    """A user, as returned to a client.

    Fields are listed explicitly -- see the module docstring. Never add
    password_hash here.
    """

    user_id: int
    user_name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
