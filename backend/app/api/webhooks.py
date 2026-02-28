"""Webhook endpoints for inbound SMS/call events.

Public endpoints protected by signature verification + rate limiting.
"""

import hashlib
import hmac
import logging
import re
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.schema import (
    AuditLog,
    ContactChannel,
    ConversationTranscript,
    InboundMessage,
    Lead,
    MessageDirection,
)
from app.workers.ai_tasks import (
    task_extract_objections,
    task_generate_transcript_summary,
    task_process_inbound_sms,
    task_run_qa_review,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Simple in-memory rate limiter
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(client_ip: str) -> bool:
    """Returns True if within rate limit, False if exceeded."""
    settings = get_settings()
    now = time.time()
    window = 60.0  # 1 minute

    # Clean old entries
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if now - t < window]
    if len(_rate_store[client_ip]) >= settings.webhook_rate_limit:
        return False
    _rate_store[client_ip].append(now)
    return True


def _normalize_phone(raw: str) -> str:
    """Normalize a phone number to last 10 digits for matching."""
    digits = re.sub(r"\D", "", raw)
    return digits[-10:] if len(digits) >= 10 else digits


def _verify_twilio_signature(request: Request, body: bytes) -> bool:
    """Verify Twilio webhook signature.

    In production (secret configured): requires valid HMAC-SHA256 signature.
    In dev (no secret + DEBUG=true): allows requests but logs a warning.
    """
    settings = get_settings()
    if not settings.twilio_webhook_secret:
        if not settings.debug:
            logger.warning(
                "Twilio webhook secret not configured — rejecting request. "
                "Set TWILIO_WEBHOOK_SECRET or enable DEBUG mode."
            )
            return False
        logger.warning("Twilio webhook secret not configured — skipping verification (DEBUG mode)")
        return True

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        return False

    expected = hmac.new(
        settings.twilio_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def _verify_webhook_api_key(request: Request) -> bool:
    """Verify webhook API key for non-Twilio endpoints.

    Checks X-Webhook-Key header against WEBHOOK_API_KEY setting.
    In dev (no key configured + DEBUG=true): allows requests but logs a warning.
    """
    settings = get_settings()
    if not settings.webhook_api_key:
        if not settings.debug:
            logger.warning(
                "Webhook API key not configured — rejecting request. "
                "Set WEBHOOK_API_KEY or enable DEBUG mode."
            )
            return False
        logger.warning("Webhook API key not configured — skipping verification (DEBUG mode)")
        return True

    provided = request.headers.get("X-Webhook-Key", "")
    if not provided:
        return False

    return hmac.compare_digest(provided, settings.webhook_api_key)


# ── Inbound SMS Webhook ──────────────────────────────────────────────────


class SMSWebhookPayload(BaseModel):
    From: str  # Twilio field names
    To: str
    Body: str
    MessageSid: str | None = None
    AccountSid: str | None = None
    NumMedia: str | None = None


@router.post("/sms", status_code=status.HTTP_200_OK)
async def sms_webhook(request: Request):
    """Twilio-compatible inbound SMS webhook handler."""
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Parse form data (Twilio sends application/x-www-form-urlencoded)
    body = await request.body()

    # Verify signature
    if not _verify_twilio_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Parse payload - Twilio sends form data
    form = await request.form()
    from_number = form.get("From", "")
    to_number = form.get("To", "")
    message_body = form.get("Body", "")
    message_sid = form.get("MessageSid", "")

    if not from_number or not message_body:
        raise HTTPException(status_code=422, detail="Missing From or Body")

    # Also support JSON payloads for testing
    if not from_number:
        import json
        try:
            data = json.loads(body)
            from_number = data.get("From", "")
            to_number = data.get("To", "")
            message_body = data.get("Body", "")
            message_sid = data.get("MessageSid", "")
        except (json.JSONDecodeError, Exception):
            raise HTTPException(status_code=422, detail="Invalid payload")

    # Find lead by phone number — normalize to last 10 digits
    from app.core.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    phone_normalized = _normalize_phone(from_number)
    if len(phone_normalized) < 10:
        logger.warning("Inbound SMS from invalid number: %s", from_number)
        return {"status": "invalid_sender"}

    async with AS(async_engine) as db:
        result = await db.execute(
            select(Lead).where(
                Lead.phone.ilike(f"%{phone_normalized}")
            ).limit(1)
        )
        lead = result.scalar_one_or_none()

        if not lead:
            logger.warning("Inbound SMS from unknown number: %s", from_number)
            return {"status": "unknown_sender"}

        # Store inbound message
        msg = InboundMessage(
            lead_id=lead.id,
            direction=MessageDirection.inbound,
            channel=ContactChannel.sms,
            from_number=from_number,
            to_number=to_number,
            body=message_body,
            external_id=message_sid,
            provider_payload=dict(form),
        )
        db.add(msg)

        db.add(AuditLog(
            actor="webhook",
            action="sms.inbound",
            entity_type="lead",
            entity_id=lead.id,
            new_value=message_body[:200],
        ))

        await db.commit()
        await db.refresh(msg)

        # Dispatch async processing
        task_process_inbound_sms.delay(msg.id)

        return {"status": "received", "message_id": msg.id}


# ── Call Outcome Webhook ─────────────────────────────────────────────────


class CallWebhookPayload(BaseModel):
    lead_id: int
    external_call_id: str | None = None
    duration_seconds: int | None = None
    transcript: str | None = None
    recording_url: str | None = None
    disposition: str | None = None
    provider_payload: dict | None = None


@router.post("/call", status_code=status.HTTP_200_OK)
async def call_webhook(payload: CallWebhookPayload, request: Request):
    """Call outcome/transcript webhook handler (provider-agnostic)."""
    client_ip = request.client.host if request.client else "unknown"

    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Verify webhook API key
    if not _verify_webhook_api_key(request):
        raise HTTPException(status_code=403, detail="Invalid webhook API key")

    from app.core.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    async with AS(async_engine) as db:
        lead = await db.get(Lead, payload.lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Store transcript if provided
        convo_id = None
        if payload.transcript:
            convo = ConversationTranscript(
                lead_id=payload.lead_id,
                channel=ContactChannel.voice,
                raw_transcript=payload.transcript,
                duration_seconds=payload.duration_seconds,
            )
            db.add(convo)
            await db.flush()
            convo_id = convo.id

            # Dispatch AI tasks
            task_generate_transcript_summary.delay(convo_id)
            task_run_qa_review.delay(convo_id)
            task_extract_objections.delay(convo_id)

        db.add(AuditLog(
            actor="webhook",
            action="call.completed",
            entity_type="lead",
            entity_id=payload.lead_id,
            new_value=payload.disposition or "unknown",
            metadata_json={"duration": payload.duration_seconds, "conversation_id": convo_id},
        ))

        await db.commit()

        return {"status": "processed", "conversation_id": convo_id}


# ── Voice Provider Webhooks ────────────────────────────────────────────


@router.post("/voice/status", status_code=status.HTTP_200_OK)
async def voice_status_webhook(request: Request):
    """Voice call status callback — works with Twilio, Vapi, Retell."""
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Verify: Twilio uses signature, others use API key
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    is_twilio = b"CallSid" in body

    if is_twilio:
        if not _verify_twilio_signature(request, body):
            raise HTTPException(status_code=403, detail="Invalid signature")
    else:
        if not _verify_webhook_api_key(request):
            raise HTTPException(status_code=403, detail="Invalid webhook API key")

    # Parse payload — could be JSON or form data
    if "json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    # Determine provider and extract call_sid
    call_sid = payload.get("call_sid") or payload.get("CallSid") or ""
    call_status_val = payload.get("status") or payload.get("CallStatus") or "unknown"
    provider_name = payload.get("provider", "twilio")

    # For Vapi, the structure is nested
    if "message" in payload:
        msg = payload["message"]
        call_data = msg.get("call", {})
        call_sid = call_data.get("id", call_sid)
        call_status_val = msg.get("type", call_status_val)
        provider_name = "vapi"

    if not call_sid:
        raise HTTPException(status_code=422, detail="Missing call_sid")

    from app.core.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    async with AS(async_engine) as db:
        result = await db.execute(
            select(ConversationTranscript)
            .where(ConversationTranscript.call_sid == call_sid)
            .limit(1)
        )
        convo = result.scalar_one_or_none()

        if convo:
            convo.call_status = call_status_val

            # Handle completion — dispatch processing task
            if call_status_val in ("completed", "ended", "end-of-call-report"):
                from app.workers.voice_tasks import task_process_call_completion
                task_process_call_completion.delay(call_sid, provider_name)

        db.add(AuditLog(
            actor="webhook",
            action="voice.status_update",
            entity_type="conversation",
            entity_id=convo.id if convo else None,
            new_value=call_status_val,
            metadata_json={"call_sid": call_sid, "provider": provider_name},
        ))

        await db.commit()

    return {"status": "received", "call_sid": call_sid}


@router.post("/voice/recording", status_code=status.HTTP_200_OK)
async def voice_recording_webhook(request: Request):
    """Voice recording ready callback — updates conversation with recording URL."""
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    body = await request.body()
    content_type = request.headers.get("content-type", "")
    is_twilio = b"CallSid" in body

    if is_twilio:
        if not _verify_twilio_signature(request, body):
            raise HTTPException(status_code=403, detail="Invalid signature")
    else:
        if not _verify_webhook_api_key(request):
            raise HTTPException(status_code=403, detail="Invalid webhook API key")

    if "json" in content_type:
        payload = await request.json()
    else:
        form = await request.form()
        payload = dict(form)

    call_sid = payload.get("CallSid") or payload.get("call_sid") or ""
    recording_url = payload.get("RecordingUrl") or payload.get("recording_url") or ""

    if not call_sid:
        raise HTTPException(status_code=422, detail="Missing call_sid")

    from app.core.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    async with AS(async_engine) as db:
        result = await db.execute(
            select(ConversationTranscript)
            .where(ConversationTranscript.call_sid == call_sid)
            .limit(1)
        )
        convo = result.scalar_one_or_none()

        if convo and recording_url:
            convo.recording_url = recording_url
            logger.info("Recording URL saved for call %s", call_sid)

        await db.commit()

    return {"status": "received"}
