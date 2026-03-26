"""Sales Board endpoints — personal KPIs, pipeline, activity for sales reps."""

from datetime import datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, case, cast, func, or_, select, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import (
    Appointment,
    AppointmentStatus,
    Lead,
    LeadScore,
    LeadStatus,
    Note,
    OutreachAttempt,
    Property,
    RepUser,
)

router = APIRouter(prefix="/sales", tags=["sales-board"], dependencies=[Depends(get_current_user)])


# ── Response Models ───────────────────────────────────────────────────────


class SalesStatsResponse(BaseModel):
    # Appointments
    appointments_today: int
    appointments_this_week: int
    appointments_completed: int
    appointments_no_show: int
    # Pipeline
    my_total_leads: int
    my_hot_leads: int
    my_warm_leads: int
    my_qualified_leads: int
    my_appointment_set: int
    # Wins / Losses
    closed_won: int
    closed_lost: int
    close_rate: float  # percentage
    # Outreach
    total_outreach: int
    calls_made: int
    sms_sent: int
    emails_sent: int
    # Follow-ups
    follow_ups_due_today: int
    avg_lead_score: float | None


class PipelineStage(BaseModel):
    stage: str
    label: str
    count: int
    leads: list[dict]


class PipelineResponse(BaseModel):
    stages: list[PipelineStage]
    total_pipeline_leads: int


class ActivityItem(BaseModel):
    id: int
    type: str  # "appointment", "outreach", "status_change", "note"
    description: str
    lead_id: int | None
    lead_name: str | None
    timestamp: str
    meta: dict | None = None


class AppointmentDetail(BaseModel):
    id: int
    lead_id: int
    lead_name: str | None
    lead_phone: str | None
    address: str | None
    status: str
    scheduled_start: str
    scheduled_end: str
    notes: str | None
    lead_score: int | None


class MyAppointmentsResponse(BaseModel):
    today: list[AppointmentDetail]
    upcoming: list[AppointmentDetail]
    recent_completed: list[AppointmentDetail]


class LeaderboardEntry(BaseModel):
    rep_id: int
    rep_name: str
    closed_won: int
    appointments_completed: int
    total_leads: int


# ── Endpoints ─────────────────────────────────────────────────────────────


@router.get("/my-stats", response_model=SalesStatsResponse)
async def get_my_stats(
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Personal KPIs for the logged-in sales rep."""
    uid = current_user.id
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
    week_start = today_start - timedelta(days=now.weekday())  # Monday

    # ── Appointments ──
    appts_today = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.rep_id == uid,
            Appointment.scheduled_start >= today_start,
            Appointment.scheduled_start <= today_end,
        )
    )).scalar() or 0

    appts_week = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.rep_id == uid,
            Appointment.scheduled_start >= week_start,
            Appointment.scheduled_start <= today_end,
        )
    )).scalar() or 0

    appts_completed = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.rep_id == uid,
            Appointment.status == AppointmentStatus.completed,
        )
    )).scalar() or 0

    appts_no_show = (await db.execute(
        select(func.count(Appointment.id)).where(
            Appointment.rep_id == uid,
            Appointment.status == AppointmentStatus.no_show,
        )
    )).scalar() or 0

    # ── My leads by status ──
    status_counts = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(Lead.assigned_rep_id == uid)
        .group_by(Lead.status)
    )
    status_map = {row[0].value: row[1] for row in status_counts.all()}

    my_total = sum(status_map.values())
    hot = status_map.get("hot", 0)
    warm = status_map.get("warm", 0)
    qualified = status_map.get("qualified", 0)
    appt_set = status_map.get("appointment_set", 0)
    won = status_map.get("closed_won", 0)
    lost = status_map.get("closed_lost", 0)

    terminal = won + lost
    close_rate = round((won / terminal * 100), 1) if terminal > 0 else 0.0

    # ── Outreach ──
    outreach_counts = await db.execute(
        select(OutreachAttempt.channel, func.count(OutreachAttempt.id))
        .join(Lead, OutreachAttempt.lead_id == Lead.id)
        .where(Lead.assigned_rep_id == uid)
        .group_by(OutreachAttempt.channel)
    )
    outreach_map = {row[0].value: row[1] for row in outreach_counts.all()}
    calls = outreach_map.get("voice", 0)
    sms = outreach_map.get("sms", 0)
    emails = outreach_map.get("email", 0)

    # ── Follow-ups due today ──
    follow_ups = (await db.execute(
        select(func.count(Lead.id)).where(
            Lead.assigned_rep_id == uid,
            Lead.next_outreach_at != None,  # noqa: E711
            Lead.next_outreach_at <= today_end,
            Lead.status.notin_([
                LeadStatus.closed_won, LeadStatus.closed_lost,
                LeadStatus.dnc, LeadStatus.archived, LeadStatus.disqualified,
            ]),
        )
    )).scalar() or 0

    # ── Avg lead score ──
    avg_score_result = (await db.execute(
        select(func.avg(LeadScore.total_score))
        .join(Lead, LeadScore.lead_id == Lead.id)
        .where(Lead.assigned_rep_id == uid)
    )).scalar()

    return SalesStatsResponse(
        appointments_today=appts_today,
        appointments_this_week=appts_week,
        appointments_completed=appts_completed,
        appointments_no_show=appts_no_show,
        my_total_leads=my_total,
        my_hot_leads=hot,
        my_warm_leads=warm,
        my_qualified_leads=qualified,
        my_appointment_set=appt_set,
        closed_won=won,
        closed_lost=lost,
        close_rate=close_rate,
        total_outreach=calls + sms + emails,
        calls_made=calls,
        sms_sent=sms,
        emails_sent=emails,
        follow_ups_due_today=follow_ups,
        avg_lead_score=round(avg_score_result, 1) if avg_score_result else None,
    )


@router.get("/my-appointments", response_model=MyAppointmentsResponse)
async def get_my_appointments(
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Today's appointments, upcoming, and recently completed for the logged-in rep."""
    uid = current_user.id
    now = datetime.now(timezone.utc)
    today_start = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
    today_end = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)

    async def build_detail(appt: Appointment) -> AppointmentDetail:
        lead = await db.get(Lead, appt.lead_id)
        lead_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip() if lead else None
        lead_phone = lead.phone if lead else None
        # Get latest score
        score_result = await db.execute(
            select(LeadScore.total_score)
            .where(LeadScore.lead_id == appt.lead_id)
            .order_by(LeadScore.scored_at.desc())
            .limit(1)
        )
        score = score_result.scalar()
        return AppointmentDetail(
            id=appt.id,
            lead_id=appt.lead_id,
            lead_name=lead_name or "Unknown",
            lead_phone=lead_phone,
            address=appt.address,
            status=appt.status.value,
            scheduled_start=appt.scheduled_start.isoformat(),
            scheduled_end=appt.scheduled_end.isoformat(),
            notes=appt.notes,
            lead_score=score,
        )

    # Today's appointments
    today_result = await db.execute(
        select(Appointment).where(
            Appointment.rep_id == uid,
            Appointment.scheduled_start >= today_start,
            Appointment.scheduled_start <= today_end,
        ).order_by(Appointment.scheduled_start.asc())
    )
    today_appts = [await build_detail(a) for a in today_result.scalars().all()]

    # Upcoming (next 7 days, excluding today)
    upcoming_result = await db.execute(
        select(Appointment).where(
            Appointment.rep_id == uid,
            Appointment.scheduled_start > today_end,
            Appointment.scheduled_start <= today_end + timedelta(days=7),
            Appointment.status.in_([AppointmentStatus.scheduled, AppointmentStatus.confirmed]),
        ).order_by(Appointment.scheduled_start.asc()).limit(20)
    )
    upcoming_appts = [await build_detail(a) for a in upcoming_result.scalars().all()]

    # Recently completed (last 7 days)
    recent_result = await db.execute(
        select(Appointment).where(
            Appointment.rep_id == uid,
            Appointment.status == AppointmentStatus.completed,
            Appointment.scheduled_start >= today_start - timedelta(days=7),
        ).order_by(Appointment.scheduled_start.desc()).limit(10)
    )
    recent_appts = [await build_detail(a) for a in recent_result.scalars().all()]

    return MyAppointmentsResponse(
        today=today_appts,
        upcoming=upcoming_appts,
        recent_completed=recent_appts,
    )


@router.get("/my-pipeline", response_model=PipelineResponse)
async def get_my_pipeline(
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pipeline breakdown by stage for the logged-in rep."""
    uid = current_user.id

    # Define pipeline stages in order
    pipeline_stages = [
        ("hot", "Hot Leads"),
        ("warm", "Warm Leads"),
        ("contacting", "Contacting"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("appointment_set", "Appointment Set"),
        ("nurturing", "Nurturing"),
        ("closed_won", "Closed Won"),
        ("closed_lost", "Closed Lost"),
    ]

    stages = []
    total = 0

    for stage_key, stage_label in pipeline_stages:
        result = await db.execute(
            select(Lead.id, Lead.first_name, Lead.last_name, Lead.phone, Lead.created_at)
            .where(
                Lead.assigned_rep_id == uid,
                Lead.status == LeadStatus(stage_key),
            )
            .order_by(Lead.updated_at.desc())
            .limit(10)
        )
        rows = result.all()
        leads = [
            {
                "id": r.id,
                "name": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Unknown",
                "phone": r.phone,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
        count_result = (await db.execute(
            select(func.count(Lead.id)).where(
                Lead.assigned_rep_id == uid,
                Lead.status == LeadStatus(stage_key),
            )
        )).scalar() or 0

        stages.append(PipelineStage(
            stage=stage_key,
            label=stage_label,
            count=count_result,
            leads=leads,
        ))
        total += count_result

    return PipelineResponse(stages=stages, total_pipeline_leads=total)


@router.get("/my-activity", response_model=list[ActivityItem])
async def get_my_activity(
    current_user: RepUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=30, le=100),
):
    """Recent activity feed for the logged-in rep's leads."""
    uid = current_user.id

    activities: list[ActivityItem] = []

    # Recent outreach attempts on my leads
    outreach_result = await db.execute(
        select(OutreachAttempt, Lead.first_name, Lead.last_name)
        .join(Lead, OutreachAttempt.lead_id == Lead.id)
        .where(Lead.assigned_rep_id == uid)
        .order_by(OutreachAttempt.started_at.desc())
        .limit(limit)
    )
    for attempt, fname, lname in outreach_result.all():
        name = f"{fname or ''} {lname or ''}".strip() or "Unknown"
        disp = attempt.disposition.value if attempt.disposition else "pending"
        activities.append(ActivityItem(
            id=attempt.id,
            type="outreach",
            description=f"{attempt.channel.value.upper()} — {disp.replace('_', ' ')}",
            lead_id=attempt.lead_id,
            lead_name=name,
            timestamp=attempt.started_at.isoformat(),
            meta={"channel": attempt.channel.value, "disposition": disp},
        ))

    # Recent appointments
    appt_result = await db.execute(
        select(Appointment, Lead.first_name, Lead.last_name)
        .join(Lead, Appointment.lead_id == Lead.id)
        .where(Appointment.rep_id == uid)
        .order_by(Appointment.created_at.desc())
        .limit(limit)
    )
    for appt, fname, lname in appt_result.all():
        name = f"{fname or ''} {lname or ''}".strip() or "Unknown"
        activities.append(ActivityItem(
            id=appt.id,
            type="appointment",
            description=f"Appointment {appt.status.value.replace('_', ' ')} — {appt.address or 'No address'}",
            lead_id=appt.lead_id,
            lead_name=name,
            timestamp=appt.scheduled_start.isoformat(),
            meta={"status": appt.status.value, "address": appt.address},
        ))

    # Recent notes on my leads
    notes_result = await db.execute(
        select(Note, Lead.first_name, Lead.last_name)
        .join(Lead, Note.lead_id == Lead.id)
        .where(Lead.assigned_rep_id == uid)
        .order_by(Note.created_at.desc())
        .limit(limit)
    )
    for note, fname, lname in notes_result.all():
        name = f"{fname or ''} {lname or ''}".strip() or "Unknown"
        preview = note.content[:80] + "..." if len(note.content) > 80 else note.content
        activities.append(ActivityItem(
            id=note.id,
            type="note",
            description=f"Note: {preview}",
            lead_id=note.lead_id,
            lead_name=name,
            timestamp=note.created_at.isoformat(),
        ))

    # Sort all by timestamp descending, limit
    activities.sort(key=lambda a: a.timestamp, reverse=True)
    return activities[:limit]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    _current_user: RepUser = Depends(get_current_user),
):
    """Team leaderboard — closed deals, completed appointments, total leads per rep."""
    result = await db.execute(
        select(
            RepUser.id,
            RepUser.name,
            func.count(Lead.id).label("total_leads"),
        )
        .outerjoin(Lead, Lead.assigned_rep_id == RepUser.id)
        .where(RepUser.is_active == True)  # noqa: E712
        .group_by(RepUser.id, RepUser.name)
    )
    reps = result.all()

    entries = []
    for rep_id, rep_name, total_leads in reps:
        won = (await db.execute(
            select(func.count(Lead.id)).where(
                Lead.assigned_rep_id == rep_id,
                Lead.status == LeadStatus.closed_won,
            )
        )).scalar() or 0

        completed = (await db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.rep_id == rep_id,
                Appointment.status == AppointmentStatus.completed,
            )
        )).scalar() or 0

        entries.append(LeaderboardEntry(
            rep_id=rep_id,
            rep_name=rep_name,
            closed_won=won,
            appointments_completed=completed,
            total_leads=total_leads,
        ))

    entries.sort(key=lambda e: e.closed_won, reverse=True)
    return entries
