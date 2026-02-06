"""Outreach endpoints — enqueue outreach, list attempts."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schema import AuditLog, Lead, OutreachAttempt
from app.services.orchestrator import enqueue_outreach

router = APIRouter(prefix="/outreach", tags=["outreach"])


class EnqueueResponse(BaseModel):
    outreach_attempt_id: int | None
    channel: str | None
    message: str


class OutreachAttemptOut(BaseModel):
    id: int
    lead_id: int
    channel: str
    disposition: str | None
    duration_seconds: int | None
    started_at: str
    ended_at: str | None


@router.post("/{lead_id}/enqueue", response_model=EnqueueResponse)
async def enqueue_outreach_endpoint(
    lead_id: int, db: AsyncSession = Depends(get_db)
):
    """Create an outreach job for the next appropriate channel."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Lead {lead_id} not found"
        )

    attempt = await enqueue_outreach(db, lead_id)

    if attempt is None:
        return EnqueueResponse(
            outreach_attempt_id=None,
            channel=None,
            message="Cannot contact this lead (DNC, exhausted attempts, or outside window)",
        )

    # Audit log
    db.add(
        AuditLog(
            actor="system",
            action="outreach.enqueued",
            entity_type="outreach_attempt",
            entity_id=attempt.id,
            new_value=f"channel={attempt.channel.value}, lead_id={lead_id}",
        )
    )

    # In production, this would also push a job to Redis/Celery.
    # For MVP, the background worker polls for pending attempts.

    return EnqueueResponse(
        outreach_attempt_id=attempt.id,
        channel=attempt.channel.value,
        message=f"Outreach enqueued via {attempt.channel.value}",
    )


@router.get("/{lead_id}/attempts", response_model=list[OutreachAttemptOut])
async def list_attempts(lead_id: int, db: AsyncSession = Depends(get_db)):
    """List all outreach attempts for a lead."""
    result = await db.execute(
        select(OutreachAttempt)
        .where(OutreachAttempt.lead_id == lead_id)
        .order_by(OutreachAttempt.started_at.desc())
    )
    attempts = result.scalars().all()
    return [
        OutreachAttemptOut(
            id=a.id,
            lead_id=a.lead_id,
            channel=a.channel.value,
            disposition=a.disposition.value if a.disposition else None,
            duration_seconds=a.duration_seconds,
            started_at=a.started_at.isoformat() if a.started_at else "",
            ended_at=a.ended_at.isoformat() if a.ended_at else None,
        )
        for a in attempts
    ]
