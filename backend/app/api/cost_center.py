"""Cost Center API — monthly cost breakdown for AI runs and voice calls."""

from calendar import monthrange
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import require_role
from app.models.schema import AIRun, ContactChannel, OutreachAttempt

router = APIRouter(
    prefix="/admin/cost-center",
    tags=["admin"],
    dependencies=[Depends(require_role("admin"))],
)


# ── Response models ─────────────────────────────────────────────────────


class DailyTotal(BaseModel):
    date: str
    ai_cost: float
    voice_cost: float


class CostSummaryResponse(BaseModel):
    month: str
    total_cost: float
    ai_cost: float
    voice_cost: float
    ai_run_count: int
    voice_call_count: int
    daily_totals: list[DailyTotal]


class CostLineItem(BaseModel):
    id: str
    category: str
    timestamp: str
    description: str
    lead_id: int | None
    detail: str
    cost_usd: float


class CostItemsResponse(BaseModel):
    items: list[CostLineItem]
    total: int
    has_more: bool


# ── Helpers ─────────────────────────────────────────────────────────────


def _parse_month(month: str | None) -> tuple[str, datetime, datetime]:
    """Parse 'YYYY-MM' to (label, start_utc, end_utc)."""
    now = datetime.now(tz=timezone.utc)
    if month:
        parts = month.split("-")
        year, mo = int(parts[0]), int(parts[1])
    else:
        year, mo = now.year, now.month

    label = f"{year}-{mo:02d}"
    start = datetime(year, mo, 1, tzinfo=timezone.utc)
    _, days = monthrange(year, mo)
    if mo == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mo + 1, 1, tzinfo=timezone.utc)
    return label, start, end


def _fmt_duration(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"


# ── Endpoints ───────────────────────────────────────────────────────────


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db),
):
    """Monthly cost summary with daily breakdown."""
    settings = get_settings()
    label, start, end = _parse_month(month)

    # AI aggregates
    ai_agg = (
        await db.execute(
            select(func.coalesce(func.sum(AIRun.cost_usd), 0), func.count(AIRun.id))
            .where(AIRun.created_at >= start, AIRun.created_at < end, AIRun.status == "success")
        )
    ).one()
    ai_cost = round(float(ai_agg[0]), 4)
    ai_count = ai_agg[1]

    # Voice call count
    voice_count = (
        await db.execute(
            select(func.count(OutreachAttempt.id)).where(
                OutreachAttempt.channel == ContactChannel.voice,
                OutreachAttempt.started_at >= start,
                OutreachAttempt.started_at < end,
            )
        )
    ).scalar() or 0

    voice_cost = round(voice_count * settings.voice_call_cost_usd, 2)

    # Daily AI costs
    ai_daily_rows = (
        await db.execute(
            select(
                cast(AIRun.created_at, Date).label("day"),
                func.coalesce(func.sum(AIRun.cost_usd), 0),
            )
            .where(AIRun.created_at >= start, AIRun.created_at < end, AIRun.status == "success")
            .group_by("day")
            .order_by("day")
        )
    ).all()
    ai_by_day = {str(row[0]): round(float(row[1]), 4) for row in ai_daily_rows}

    # Daily voice counts
    voice_daily_rows = (
        await db.execute(
            select(
                cast(OutreachAttempt.started_at, Date).label("day"),
                func.count(OutreachAttempt.id),
            )
            .where(
                OutreachAttempt.channel == ContactChannel.voice,
                OutreachAttempt.started_at >= start,
                OutreachAttempt.started_at < end,
            )
            .group_by("day")
            .order_by("day")
        )
    ).all()
    voice_by_day = {str(row[0]): row[1] for row in voice_daily_rows}

    # Merge into daily totals for every day of the month
    _, days_in_month = monthrange(start.year, start.month)
    today = datetime.now(tz=timezone.utc).date()
    daily_totals = []
    for d in range(1, days_in_month + 1):
        day_date = start.replace(day=d).date()
        if day_date > today:
            break
        day_str = str(day_date)
        daily_totals.append(
            DailyTotal(
                date=day_str,
                ai_cost=ai_by_day.get(day_str, 0),
                voice_cost=round(voice_by_day.get(day_str, 0) * settings.voice_call_cost_usd, 2),
            )
        )

    return CostSummaryResponse(
        month=label,
        total_cost=round(ai_cost + voice_cost, 2),
        ai_cost=ai_cost,
        voice_cost=voice_cost,
        ai_run_count=ai_count,
        voice_call_count=voice_count,
        daily_totals=daily_totals,
    )


@router.get("/items", response_model=CostItemsResponse)
async def get_cost_items(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    category: str = Query("all"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Paginated cost line items combining AI runs and voice calls."""
    settings = get_settings()
    _, start, end = _parse_month(month)

    items: list[CostLineItem] = []
    ai_total = 0
    voice_total = 0

    # AI runs
    if category in ("all", "ai"):
        ai_total = (
            await db.execute(
                select(func.count(AIRun.id)).where(
                    AIRun.created_at >= start, AIRun.created_at < end, AIRun.status == "success"
                )
            )
        ).scalar() or 0

        ai_rows = (
            await db.execute(
                select(AIRun)
                .where(AIRun.created_at >= start, AIRun.created_at < end, AIRun.status == "success")
                .order_by(AIRun.created_at.desc())
            )
        ).scalars().all()

        for run in ai_rows:
            tokens = (run.tokens_in or 0) + (run.tokens_out or 0)
            items.append(
                CostLineItem(
                    id=f"ai-{run.id}",
                    category="ai",
                    timestamp=run.created_at.isoformat(),
                    description=f"{run.task_type} — {run.model}",
                    lead_id=run.lead_id,
                    detail=f"{tokens:,} tokens",
                    cost_usd=round(run.cost_usd or 0, 4),
                )
            )

    # Voice calls
    if category in ("all", "voice"):
        voice_total = (
            await db.execute(
                select(func.count(OutreachAttempt.id)).where(
                    OutreachAttempt.channel == ContactChannel.voice,
                    OutreachAttempt.started_at >= start,
                    OutreachAttempt.started_at < end,
                )
            )
        ).scalar() or 0

        voice_rows = (
            await db.execute(
                select(OutreachAttempt)
                .where(
                    OutreachAttempt.channel == ContactChannel.voice,
                    OutreachAttempt.started_at >= start,
                    OutreachAttempt.started_at < end,
                )
                .order_by(OutreachAttempt.started_at.desc())
            )
        ).scalars().all()

        for call in voice_rows:
            items.append(
                CostLineItem(
                    id=f"voice-{call.id}",
                    category="voice",
                    timestamp=call.started_at.isoformat(),
                    description=f"Outbound call — {settings.voice_provider}",
                    lead_id=call.lead_id,
                    detail=_fmt_duration(call.duration_seconds),
                    cost_usd=settings.voice_call_cost_usd,
                )
            )

    # Sort merged list by timestamp descending, apply pagination
    items.sort(key=lambda x: x.timestamp, reverse=True)
    total = ai_total + voice_total
    page = items[offset : offset + limit]

    return CostItemsResponse(
        items=page,
        total=total,
        has_more=(offset + limit) < total,
    )
