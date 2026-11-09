"""Dashboard response.

Task 64. Field names follow `frontend/src/mocks/dashboard.js` so Task 87
can switch source without reshaping the page.

ONE FIELD IS DELIBERATELY NULLABLE WHERE THE MOCK HAD A NUMBER.

The mock supplies `avgResponseTimeMs: 420`. Nothing stored that, so
Task 64 added `AnalysisResult.latency_ms` and measures it rather than
returning a plausible-looking constant. It is null until the caller has
at least one analysis with a recorded measurement -- rows created before
that column existed have none, and counting them as 0 would drag the
average down with fabricated data.

THE MOCK'S `attackFrequency` USED NUMBERED SAMPLE POINTS, NOT DATES.

Its own comment says so: "Numbered sample points, not dates: there is no
real time period behind them." This returns real dates, because there
now is one.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ActivityPoint(BaseModel):
    """One day's attack counts, for the chart."""

    # ISO date. The mock used 'Sample 1' labels because it had no real
    # period; this has one.
    day: date
    directJailbreak: int = 0
    indirectInjection: int = 0
    safe: int = 0


class RecentAnalysis(BaseModel):
    """A compact row for the dashboard's recent-activity list.

    Deliberately NOT the full history item: the dashboard shows a
    glance, and `GET /api/history` already serves the detailed list.
    Prompt text is truncated server-side so a 3,900-token attack cannot
    arrive in a summary payload.
    """

    promptId: int
    promptPreview: str
    classification: str | None = None
    subtype: str | None = None
    severity: str | None = None
    analysedAt: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """Aggregate stats for the signed-in user.

    Scoped to the caller, like history. A shared dashboard would leak
    one user's prompt volume and attack mix to another.
    """

    totalAnalyses: int = 0
    totalPrompts: int = 0

    # Per 3-class label. Always contains all three keys, including zeros
    # -- a missing key would make the UI render a gap rather than a 0,
    # and "no Indirect attacks yet" is information.
    countsByClass: dict[str, int] = Field(default_factory=dict)

    # Per sub-type. Always all eight keys, same reasoning. The frontend
    # mock deliberately showed Role Override as 0 to exercise the
    # zero-count row, and it will genuinely be 0 here -- the sub-type
    # model never predicts it (ML Task 34).
    countsBySubtype: dict[str, int] = Field(default_factory=dict)

    attackFrequency: list[ActivityPoint] = Field(default_factory=list)
    recentActivity: list[RecentAnalysis] = Field(default_factory=list)

    # Null until there is a measured analysis -- see the module note.
    avgResponseTimeMs: float | None = None

    # Simulation Lab progress (Tasks 62-63).
    simulationsStarted: int = 0
    simulationsCompleted: int = 0
