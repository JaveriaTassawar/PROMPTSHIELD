"""Prompt analysis endpoint.

Task 56. Where the classifier meets the API.

FOUR DECISIONS:

1. THE PROMPT IS STORED BEFORE IT IS CLASSIFIED.

   The row is written with status `pending` first, then updated once the
   result arrives. If classification fails, the prompt is still on record
   with an honest status -- which is what an audit of a security tool
   needs. Classifying first and storing afterwards would lose every
   prompt that crashed the model, and those are exactly the interesting
   ones.

2. EVERYTHING COMMITS IN ONE TRANSACTION.

   The prompt, its analysis and its sub-type are written together. A
   partial commit would leave an analysed prompt with no analysis row, or
   a sub-type pointing at nothing -- states the Task 60-63 analytics have
   no way to interpret.

3. A MISSING MODEL IS 503, NOT 500.

   `ClassifierUnavailable` means the endpoint is fine and the capability
   is not. 503 tells a client to retry later; 500 says we have a bug.
   The prompt row is left `pending` so it can be re-analysed once the
   model is configured.

4. THE ENDPOINT REQUIRES AUTHENTICATION.

   The plan does not say so explicitly, but `Prompt.user_id` exists and
   the dashboard in Task 60 shows "my prompts". An anonymous endpoint
   would have nothing to attribute rows to, and would let anyone spend
   the server's inference budget.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.analysis import AnalysisResult
from app.models.prompt import Prompt
from app.models.subtype import AttackSubtype
from app.models.suggestion import SafeSuggestion
from app.models.user import User
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    SafePromptRequest,
    SafePromptResponse,
)
from app.services.classifier import ClassifierUnavailable, classify_prompt
from app.services.mitigation import build_suggestion

router = APIRouter(prefix="/api", tags=["analysis"])

UNAVAILABLE_DETAIL = (
    "The classification model is not available. The prompt has been saved "
    "and can be analysed once the model is configured."
)


@router.post(
    "/analyze-prompt",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "Missing or invalid token"},
        422: {"description": "Empty prompt, or longer than the limit"},
        503: {"description": UNAVAILABLE_DETAIL},
    },
)
def analyze_prompt(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnalyzeResponse:
    """Classify a prompt and record the result."""
    # Stored first -- see decision 1.
    prompt = Prompt(user_id=user.user_id, prompt_text=payload.prompt)
    db.add(prompt)
    db.flush()  # assigns prompt_id without committing

    try:
        result = classify_prompt(payload.prompt)
    except ClassifierUnavailable:
        # Keep the prompt, marked honestly. Committing here rather than
        # rolling back is the point of decision 1.
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=UNAVAILABLE_DETAIL,
        ) from None
    except ValueError as exc:
        # The ML and backend label sets have drifted. A 500 is correct:
        # this is a deployment bug, not something the caller can fix.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    prompt.status = "analyzed"

    analysis = AnalysisResult(
        prompt_id=prompt.prompt_id,
        detection_result=result.is_attack,
        prompt_type=result.label,
        severity_level=result.severity,
        confidence_score=result.confidence,
    )
    db.add(analysis)
    db.flush()

    if result.subtype is not None:
        db.add(
            AttackSubtype(
                analysis_id=analysis.analysis_id,
                subtype_name=result.subtype,
                confidence=result.subtype_confidence,
            )
        )

    # Task 59: the safer-phrasing suggestion, stored alongside (Task 46)
    # so /api/history and the dashboard can show it without recomputing.
    # None for Safe prompts, which is the correct answer rather than a gap.
    suggestion = build_suggestion(payload.prompt, result.label, result.subtype)
    if suggestion is not None:
        db.add(
            SafeSuggestion(
                analysis_id=analysis.analysis_id,
                suggested_prompt=suggestion.suggested_prompt,
                suggestion_reason=suggestion.reason,
            )
        )

    # One commit for all of it -- see decision 2.
    db.commit()

    return AnalyzeResponse(
        promptId=prompt.prompt_id,
        classification=result.label,
        subtype=result.subtype,
        severity=result.severity,
        confidenceScore=result.confidence,
        subtypeConfidence=result.subtype_confidence,
        subtypeReliable=result.subtype_reliable,
        safePromptSuggestion=(
            suggestion.suggested_prompt if suggestion is not None else None
        ),
        # Task 82 fills this; the frontend renders its own guidance today.
        avatarFeedback=None,
    )


@router.post(
    "/safe-prompt",
    response_model=SafePromptResponse,
    responses={
        401: {"description": "Missing or invalid token"},
        404: {"description": "promptId does not belong to the caller"},
        422: {"description": "Unknown classification, or prompt too long"},
    },
)
def safe_prompt(
    payload: SafePromptRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SafePromptResponse:
    """A safer way to ask the same thing.

    Task 59. Rule and template based -- no LLM call, which the plan
    specifies and which also avoids a real hazard: a model asked to
    rewrite a jailbreak is itself a target for that jailbreak. Sending
    attack text to a generative model and showing the user its output
    would be a prompt-injection vulnerability inside a prompt-injection
    detector.

    Takes the classification rather than re-running the model, since the
    caller already has it from /api/analyze-prompt.

    `promptId` is optional. Supplied, the suggestion is stored against
    that analysis; omitted, advice is returned without persisting --
    which the Learning Hub needs for example prompts that are not a
    user's own submission.
    """
    try:
        suggestion = build_suggestion(
            payload.prompt, payload.classification, payload.subtype
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if suggestion is None:
        # Safe prompt. Not an error -- there is nothing to teach.
        return SafePromptResponse()

    if payload.promptId is not None:
        prompt = db.get(Prompt, payload.promptId)

        # Checked against the caller, not just existence. Without this,
        # any authenticated user could attach a suggestion to another
        # user's prompt by guessing an id.
        if prompt is None or prompt.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No such prompt for this account.",
            )

        if prompt.analysis is not None:
            existing = prompt.analysis.suggestion
            if existing is None:
                db.add(
                    SafeSuggestion(
                        analysis_id=prompt.analysis.analysis_id,
                        suggested_prompt=suggestion.suggested_prompt,
                        suggestion_reason=suggestion.reason,
                    )
                )
            else:
                # Task 46 made analysis_id unique, so regenerating
                # updates rather than appending a row the API would then
                # have to choose between.
                existing.suggested_prompt = suggestion.suggested_prompt
                existing.suggestion_reason = suggestion.reason
            db.commit()

    return SafePromptResponse(
        suggestedPrompt=suggestion.suggested_prompt,
        reason=suggestion.reason,
        isTemplate=suggestion.is_template,
    )
