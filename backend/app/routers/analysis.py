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
from app.models.user import User
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.classifier import ClassifierUnavailable, classify_prompt

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
        # Task 57 fills this; Task 82 fills avatarFeedback.
        safePromptSuggestion=None,
        avatarFeedback=None,
    )
