"""Next-Best-Action endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import Lead, NBADecision
from app.workers.ai_tasks import task_nba_decide

router = APIRouter(
    prefix="/leads",
    tags=["nba"],
    dependencies=[Depends(get_current_user)],
)


class NBADecisionOut(BaseModel):
    id: int
    lead_id: int
    recommended_action: str
    recommended_channel: str | None
    schedule_time: str | None
    reason_codes: list | None
    confidence: float
    applied: bool
    expires_at: str | None
    created_at: str


@router.get("/{lead_id}/nba", response_model=NBADecisionOut | None)
async def get_lead_nba(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get the latest NBA decision for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(NBADecision)
        .where(NBADecision.lead_id == lead_id)
        .order_by(NBADecision.created_at.desc())
        .limit(1)
    )
    decision = result.scalar_one_or_none()

    if not decision:
        return None

    return NBADecisionOut(
        id=decision.id,
        lead_id=decision.lead_id,
        recommended_action=decision.recommended_action.value,
        recommended_channel=decision.recommended_channel.value if decision.recommended_channel else None,
        schedule_time=decision.schedule_time.isoformat() if decision.schedule_time else None,
        reason_codes=decision.reason_codes,
        confidence=decision.confidence,
        applied=decision.applied,
        expires_at=decision.expires_at.isoformat() if decision.expires_at else None,
        created_at=decision.created_at.isoformat() if decision.created_at else "",
    )


@router.post("/{lead_id}/nba/recompute", response_model=dict)
async def recompute_nba(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger NBA recomputation for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    task_nba_decide.delay(lead_id)
    return {"status": "computing", "lead_id": lead_id}
