"""Dashboard endpoints — KPIs, charts, summary stats."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import (
    Appointment,
    AppointmentStatus,
    Lead,
    LeadScore,
    LeadStatus,
    OutreachAttempt,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


class KPIResponse(BaseModel):
    total_leads: int
    hot_leads: int
    warm_leads: int
    cool_leads: int
    appointments_scheduled: int
    appointments_completed: int
    total_outreach_attempts: int
    avg_score: float | None
    conversion_rate: float
    status_breakdown: dict[str, int]


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(db: AsyncSession = Depends(get_db)):
    """Return dashboard KPIs for the overview page."""
    # Total leads
    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar() or 0

    # Status counts
    status_result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    status_breakdown = {row[0].value: row[1] for row in status_result.all()}

    hot_leads = status_breakdown.get("hot", 0)
    warm_leads = status_breakdown.get("warm", 0)
    cool_leads = status_breakdown.get("cool", 0)

    # Appointments
    appt_scheduled = (
        await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.status == AppointmentStatus.scheduled
            )
        )
    ).scalar() or 0

    appt_completed = (
        await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.status == AppointmentStatus.completed
            )
        )
    ).scalar() or 0

    # Outreach
    total_outreach = (
        await db.execute(select(func.count(OutreachAttempt.id)))
    ).scalar() or 0

    # Avg score
    avg_score = (
        await db.execute(select(func.avg(LeadScore.total_score)))
    ).scalar()

    # Conversion rate: leads with appointment / total scored leads
    scored_count = sum(
        v for k, v in status_breakdown.items() if k not in ("ingested",)
    )
    appointment_count = status_breakdown.get("appointment_set", 0) + status_breakdown.get(
        "closed_won", 0
    )
    conversion_rate = (appointment_count / scored_count * 100) if scored_count > 0 else 0.0

    return KPIResponse(
        total_leads=total_leads,
        hot_leads=hot_leads,
        warm_leads=warm_leads,
        cool_leads=cool_leads,
        appointments_scheduled=appt_scheduled,
        appointments_completed=appt_completed,
        total_outreach_attempts=total_outreach,
        avg_score=round(avg_score, 1) if avg_score else None,
        conversion_rate=round(conversion_rate, 1),
        status_breakdown=status_breakdown,
    )
