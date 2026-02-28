"""Dashboard insights endpoint — AI-generated weekly summary."""

import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import (
    InboundMessage,
    Lead,
    LeadScore,
    LeadStatus,
    MessageDirection,
    NBADecision,
    ObjectionTag,
    QAReview,
)
from app.services.ai_client import get_ai_client
from app.services.prompts import INSIGHTS_SYSTEM, INSIGHTS_USER, render_template

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


class InsightsResponse(BaseModel):
    narrative: str
    key_drivers: list[str]
    recommendations: list[str]


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(db: AsyncSession = Depends(get_db)):
    """Weekly AI summary narrative with key drivers."""
    # Gather KPI data
    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar() or 0

    status_result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    status_map = {row[0].value: row[1] for row in status_result.all()}
    hot_leads = status_map.get("hot", 0)
    appointments_set = status_map.get("appointment_set", 0)

    # Avg score
    avg_score = (await db.execute(select(func.avg(LeadScore.total_score)))).scalar()
    avg_score = round(avg_score, 1) if avg_score else 0

    # Conversion rate
    scored = sum(v for k, v in status_map.items() if k != "ingested")
    appt_count = status_map.get("appointment_set", 0) + status_map.get("closed_won", 0)
    conversion_rate = round(appt_count / scored * 100, 1) if scored > 0 else 0.0

    # Top objections
    objections = await db.execute(
        select(ObjectionTag.tag, func.count(ObjectionTag.id))
        .group_by(ObjectionTag.tag)
        .order_by(func.count(ObjectionTag.id).desc())
        .limit(5)
    )
    top_objections = ", ".join(f"{t} ({c})" for t, c in objections.all()) or "None yet"

    # SMS response rate
    total_outbound_sms = (await db.execute(
        select(func.count(InboundMessage.id))
        .where(InboundMessage.direction == MessageDirection.outbound)
    )).scalar() or 0
    total_inbound_sms = (await db.execute(
        select(func.count(InboundMessage.id))
        .where(InboundMessage.direction == MessageDirection.inbound)
    )).scalar() or 0
    sms_response_rate = round(
        total_inbound_sms / total_outbound_sms * 100, 1
    ) if total_outbound_sms > 0 else 0.0

    # QA avg compliance
    qa_avg = (await db.execute(select(func.avg(QAReview.compliance_score)))).scalar()
    qa_avg_score = round(qa_avg, 1) if qa_avg else 0

    # Generate AI narrative
    ai = get_ai_client()
    user_prompt = render_template(
        INSIGHTS_USER,
        total_leads=str(total_leads),
        leads_delta="+0",  # TODO: compute delta from previous week
        hot_leads=str(hot_leads),
        appointments_set=str(appointments_set),
        conversion_rate=str(conversion_rate),
        avg_score=str(avg_score),
        top_objections=top_objections,
        sms_response_rate=str(sms_response_rate),
        qa_avg_score=str(qa_avg_score),
    )

    result = await ai.chat(INSIGHTS_SYSTEM, user_prompt)

    return InsightsResponse(
        narrative=result.get("narrative", "No insights available yet. Add more data to see AI-generated analysis."),
        key_drivers=result.get("key_drivers", []),
        recommendations=result.get("recommendations", []),
    )
