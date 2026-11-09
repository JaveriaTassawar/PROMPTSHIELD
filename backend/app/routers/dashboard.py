"""Dashboard endpoint.

Task 64. Aggregate stats for the signed-in user.

FOUR DECISIONS:

1. AGGREGATED IN SQL, NOT IN PYTHON.

   The obvious implementation loads the caller's analyses and counts them
   in a loop. That works at ten rows and falls over at ten thousand: it
   transfers every row to count them. These are GROUP BY queries, so the
   database returns one row per class and per sub-type regardless of how
   many analyses sit behind them.

2. ZERO COUNTS ARE PRESENT, NOT OMITTED.

   A GROUP BY only returns groups that exist. Returning that directly
   would give the UI `{"Safe": 3}` and no Direct Jailbreak key, which
   renders as a gap rather than a zero -- and "no Indirect attacks yet"
   is information worth showing. Every class and sub-type key is seeded
   to 0 first.

   Role Override will genuinely read 0: the sub-type model never
   predicts it (ML Task 34).

3. SCOPED TO THE CALLER, WITH NO user_id PARAMETER.

   Same reasoning as /api/profile and /api/history. A dashboard is a
   summary of one person's prompt volume and attack mix, which is not
   another user's business.

4. THE AVERAGE EXCLUDES UNMEASURED ROWS.

   `latency_ms` is null for analyses created before Task 64 added the
   column. AVG ignores nulls, which is the right behaviour -- treating
   them as 0 would report a fabricated sub-millisecond average.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.analysis import PROMPT_TYPES, AnalysisResult
from app.models.prompt import Prompt
from app.models.simulation import SimulationSession
from app.models.subtype import SUBTYPE_NAMES, AttackSubtype
from app.models.user import User
from app.schemas.dashboard import (
    ActivityPoint,
    DashboardResponse,
    RecentAnalysis,
)

router = APIRouter(prefix="/api", tags=["dashboard"])

# How much prompt text the recent-activity list carries. The dashboard
# shows a glance; /api/history serves the full text. Truncating here
# stops a 3,900-token attack arriving in a summary payload.
PREVIEW_CHARS = 80

RECENT_LIMIT = 5

# Days of history in the activity chart.
ACTIVITY_DAYS = 7


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    responses={401: {"description": "Missing or invalid token"}},
)
def dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    days: int = Query(ACTIVITY_DAYS, ge=1, le=90),
) -> DashboardResponse:
    """Aggregate stats for the signed-in user."""
    total_prompts = (
        db.scalar(
            select(func.count())
            .select_from(Prompt)
            .where(Prompt.user_id == user.user_id)
        )
        or 0
    )

    # Every analysis belonging to this user, via their prompts.
    mine = select(AnalysisResult.analysis_id).join(Prompt).where(
        Prompt.user_id == user.user_id
    )

    total_analyses = db.scalar(
        select(func.count()).select_from(mine.subquery())
    ) or 0

    # --- counts per class (decision 1) -----------------------------------
    # Seeded with zeros first -- see decision 2.
    counts_by_class = {label: 0 for label in PROMPT_TYPES}
    for label, count in db.execute(
        select(AnalysisResult.prompt_type, func.count())
        .join(Prompt)
        .where(Prompt.user_id == user.user_id)
        .group_by(AnalysisResult.prompt_type)
    ):
        counts_by_class[label] = count

    # --- counts per sub-type ---------------------------------------------
    counts_by_subtype = {name: 0 for name in SUBTYPE_NAMES}
    for name, count in db.execute(
        select(AttackSubtype.subtype_name, func.count())
        .join(AnalysisResult, AttackSubtype.analysis_id == AnalysisResult.analysis_id)
        .join(Prompt, AnalysisResult.prompt_id == Prompt.prompt_id)
        .where(Prompt.user_id == user.user_id)
        .group_by(AttackSubtype.subtype_name)
    ):
        counts_by_subtype[name] = count

    # --- activity over time ----------------------------------------------
    # Every day in the window appears, including empty ones: a chart that
    # silently drops quiet days compresses the x-axis and misleads.
    today = date.today()
    window_start = today - timedelta(days=days - 1)
    buckets: dict[date, dict[str, int]] = {
        window_start + timedelta(days=offset): {
            "Safe": 0,
            "Direct Jailbreak": 0,
            "Indirect Injection": 0,
        }
        for offset in range(days)
    }

    for day_text, label, count in db.execute(
        select(
            func.date(AnalysisResult.analysed_at),
            AnalysisResult.prompt_type,
            func.count(),
        )
        .join(Prompt)
        .where(
            Prompt.user_id == user.user_id,
            func.date(AnalysisResult.analysed_at) >= window_start.isoformat(),
        )
        .group_by(func.date(AnalysisResult.analysed_at), AnalysisResult.prompt_type)
    ):
        try:
            day = date.fromisoformat(str(day_text))
        except ValueError:
            continue
        if day in buckets:
            buckets[day][label] = count

    activity = [
        ActivityPoint(
            day=day,
            safe=counts["Safe"],
            directJailbreak=counts["Direct Jailbreak"],
            indirectInjection=counts["Indirect Injection"],
        )
        for day, counts in sorted(buckets.items())
    ]

    # --- recent activity --------------------------------------------------
    recent = []
    for prompt, analysis in db.execute(
        select(Prompt, AnalysisResult)
        .outerjoin(AnalysisResult, AnalysisResult.prompt_id == Prompt.prompt_id)
        .where(Prompt.user_id == user.user_id)
        .order_by(Prompt.submission_time.desc(), Prompt.prompt_id.desc())
        .limit(RECENT_LIMIT)
    ):
        text = prompt.prompt_text or ""
        preview = text[:PREVIEW_CHARS]
        if len(text) > PREVIEW_CHARS:
            preview += "..."

        recent.append(
            RecentAnalysis(
                promptId=prompt.prompt_id,
                promptPreview=preview,
                classification=analysis.prompt_type if analysis else None,
                subtype=(
                    analysis.subtype.subtype_name
                    if analysis is not None and analysis.subtype is not None
                    else None
                ),
                severity=analysis.severity_level if analysis else None,
                analysedAt=(
                    analysis.analysed_at.isoformat() if analysis else None
                ),
            )
        )

    # --- average latency (decision 4) ------------------------------------
    avg_latency = db.scalar(
        select(func.avg(AnalysisResult.latency_ms))
        .join(Prompt)
        .where(
            Prompt.user_id == user.user_id,
            AnalysisResult.latency_ms.is_not(None),
        )
    )

    # --- simulation progress ---------------------------------------------
    sims_started = (
        db.scalar(
            select(func.count())
            .select_from(SimulationSession)
            .where(SimulationSession.user_id == user.user_id)
        )
        or 0
    )
    sims_completed = (
        db.scalar(
            select(func.count())
            .select_from(SimulationSession)
            .where(
                SimulationSession.user_id == user.user_id,
                SimulationSession.outcome == "completed",
            )
        )
        or 0
    )

    return DashboardResponse(
        totalAnalyses=total_analyses,
        totalPrompts=total_prompts,
        countsByClass=counts_by_class,
        countsBySubtype=counts_by_subtype,
        attackFrequency=activity,
        recentActivity=recent,
        avgResponseTimeMs=(
            round(float(avg_latency), 2) if avg_latency is not None else None
        ),
        simulationsStarted=sims_started,
        simulationsCompleted=sims_completed,
    )
