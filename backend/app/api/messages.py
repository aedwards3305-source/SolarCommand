"""Message thread endpoints for leads."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.schema import (
    AuditLog,
    ContactChannel,
    InboundMessage,
    Lead,
    MessageDirection,
)
from app.services.compliance import check_can_message
from app.workers.ai_tasks import task_send_sms

router = APIRouter(prefix="/leads", tags=["messages"], dependencies=[Depends(get_current_user)])


class MessageOut(BaseModel):
    id: int
    direction: str
    channel: str
    from_number: str | None
    to_number: str | None
    body: str
    ai_intent: str | None
    ai_suggested_reply: str | None
    sent_by: str | None
    created_at: str


class SendMessageRequest(BaseModel):
    message: str
    script_version_id: int | None = None


@router.get("/{lead_id}/messages", response_model=list[MessageOut])
async def get_messages(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get the message thread for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(InboundMessage)
        .where(InboundMessage.lead_id == lead_id)
        .order_by(InboundMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        MessageOut(
            id=m.id,
            direction=m.direction.value,
            channel=m.channel.value if m.channel else "sms",
            from_number=m.from_number,
            to_number=m.to_number,
            body=m.body,
            ai_intent=m.ai_intent,
            ai_suggested_reply=m.ai_suggested_reply,
            sent_by=m.sent_by,
            created_at=m.created_at.isoformat() if m.created_at else "",
        )
        for m in messages
    ]


@router.post("/{lead_id}/messages/send", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def send_message(
    lead_id: int,
    payload: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Send an SMS message to a lead (enqueues Celery job)."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if not lead.phone:
        raise HTTPException(status_code=422, detail="Lead has no phone number")

    # Compliance check
    allowed, reason = await check_can_message(db, lead)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Cannot message lead: {reason}")

    # Record the outbound message immediately for UI
    from app.core.config import get_settings
    settings = get_settings()

    msg = InboundMessage(
        lead_id=lead_id,
        direction=MessageDirection.outbound,
        channel=ContactChannel.sms,
        from_number=settings.twilio_phone_number or "+10000000000",
        to_number=lead.phone,
        body=payload.message,
        sent_by=f"rep:{current_user.email}",
        script_version_id=payload.script_version_id,
    )
    db.add(msg)

    db.add(AuditLog(
        actor=current_user.email,
        action="sms.sent_by_rep",
        entity_type="lead",
        entity_id=lead_id,
        new_value=payload.message[:200],
    ))

    await db.flush()

    # Enqueue the actual send
    task_send_sms.delay(lead_id, payload.message, payload.script_version_id)

    return {"status": "queued", "message_id": msg.id}
