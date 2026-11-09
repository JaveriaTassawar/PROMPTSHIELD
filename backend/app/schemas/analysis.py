"""Request and response bodies for prompt analysis.

Task 56. The response follows SDS §6.5, which both the frontend and
backend TASKS.md quote.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Task 42 stores prompt_text as Text with no length cap, because real
# attacks reach ~3,900 tokens. The cap belongs here instead: rejecting
# oversized input with 422 at the edge beats a 500 from the database, and
# beats spending GPU time tokenising something absurd.
#
# 20,000 characters is roughly 5,000 tokens -- comfortably above the
# longest prompt measured in the ML work, and far below anything that
# would be a denial-of-service payload.
MAX_PROMPT_CHARS = 20_000


class AnalyzeRequest(BaseModel):
    """Body of POST /api/analyze-prompt."""

    prompt: str = Field(
        min_length=1,
        max_length=MAX_PROMPT_CHARS,
        description="The prompt text to classify.",
    )


class AnalyzeResponse(BaseModel):
    """SDS §6.5 response shape.

    Field names are camelCase to match what the frontend already expects
    -- see the contract in backend/TASKS.md. `subtype`, `severity` and
    the rest keep the names the frontend mocks use.

    `subtype` is null for Safe prompts AND whenever the optional
    sub-type model is not configured (Task 35). `avatarFeedback` is null
    until Task 82 -- the frontend renders its own guidance today (Task 47).
    """

    promptId: int
    classification: str
    subtype: str | None = None
    severity: str
    confidenceScore: float
    subtypeConfidence: float | None = None

    # False when the sub-type was predicted by a class the ML model
    # cannot reliably identify -- Role Override scores 0.00 F1 and is
    # never predicted, so a returned "Policy Evasion" may be wrong in
    # that direction. See ml/MODEL_CARD.md 19.7.
    subtypeReliable: bool = True

    safePromptSuggestion: str | None = None
    avatarFeedback: str | None = None

    model_config = ConfigDict(from_attributes=True)
