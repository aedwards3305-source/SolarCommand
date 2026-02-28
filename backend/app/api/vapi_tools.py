"""Vapi server-side tool endpoints.

When Vapi's AI agent invokes a tool (function call), Vapi sends a POST to
the assistant's serverUrl. This router handles those tool invocations:
  - schedule_appointment: creates an Appointment + updates lead status
  - schedule_callback: creates an OutreachAttempt with callback time
  - log_call_outcome: records the call disposition
"""

import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_engine
from app.models.schema import (
    Appointment,
    AppointmentStatus,
    AuditLog,
    ContactChannel,
    ContactDisposition,
    ConversationTranscript,
    Lead,
    LeadStatus,
    OutreachAttempt,
    Property,
    RepUser,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi-tools"])

ET = ZoneInfo("America/New_York")

# Map Rebecca's tool dispositions → ContactDisposition enum
_DISPOSITION_MAP = {
    "appointment_booked": ContactDisposition.appointment_booked,
    "callback_scheduled": ContactDisposition.callback_scheduled,
    "not_interested": ContactDisposition.not_interested,
    "not_qualified": ContactDisposition.not_interested,
    "wrong_number": ContactDisposition.wrong_number,
    "voicemail": ContactDisposition.voicemail,
    "no_answer": ContactDisposition.no_answer,
    "dnc": ContactDisposition.do_not_call,
    "renter": ContactDisposition.not_homeowner,
    "already_has_solar": ContactDisposition.not_interested,
    "busy_callback_refused": ContactDisposition.not_interested,
}

# Map dispositions → lead status transitions
_STATUS_MAP = {
    "appointment_booked": LeadStatus.appointment_set,
    "callback_scheduled": LeadStatus.contacted,
    "not_interested": LeadStatus.closed_lost,
    "not_qualified": LeadStatus.disqualified,
    "dnc": LeadStatus.dnc,
    "renter": LeadStatus.disqualified,
    "voicemail": LeadStatus.contacting,
    "no_answer": LeadStatus.contacting,
}


def _normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    return digits[-10:] if len(digits) >= 10 else digits


async def _find_lead_by_phone(db: AsyncSession, phone: str) -> Lead | None:
    normalized = _normalize_phone(phone)
    if len(normalized) < 10:
        return None
    result = await db.execute(
        select(Lead).where(Lead.phone.ilike(f"%{normalized}")).limit(1)
    )
    return result.scalar_one_or_none()


async def _get_available_rep(db: AsyncSession, lead: Lead) -> RepUser | None:
    """Return the lead's assigned rep, or the first active rep."""
    if lead.assigned_rep_id:
        return await db.get(RepUser, lead.assigned_rep_id)
    result = await db.execute(
        select(RepUser).where(RepUser.is_active.is_(True)).limit(1)
    )
    return result.scalar_one_or_none()


# ── Main Vapi Server URL Endpoint ──────────────────────────────────────


@router.post("/server", status_code=status.HTTP_200_OK)
async def vapi_server_handler(request: Request):
    """Handle all Vapi server URL callbacks (function calls + status events).

    Vapi sends POST requests here for:
    - Function calls (tool invocations from the AI agent)
    - Call status updates
    - End-of-call reports
    """
    settings = get_settings()

    # Verify webhook secret if configured
    if settings.webhook_api_key:
        secret = request.headers.get("X-Vapi-Secret", "")
        if secret != settings.webhook_api_key:
            raise HTTPException(status_code=403, detail="Invalid server URL secret")

    payload = await request.json()
    message = payload.get("message", {})
    msg_type = message.get("type", "")

    # Route by message type
    if msg_type == "function-call":
        return await _handle_function_call(message)
    elif msg_type in ("status-update", "end-of-call-report"):
        logger.info("Vapi %s: %s", msg_type, message.get("call", {}).get("id", ""))
        return {"result": "acknowledged"}
    elif msg_type == "hang":
        return {"result": "acknowledged"}
    else:
        logger.debug("Vapi unhandled message type: %s", msg_type)
        return {"result": "acknowledged"}


async def _handle_function_call(message: dict) -> dict:
    """Dispatch a Vapi function call to the appropriate handler."""
    fn_call = message.get("functionCall", {})
    fn_name = fn_call.get("name", "")
    params = fn_call.get("parameters", {})
    call_data = message.get("call", {})
    customer_number = call_data.get("customer", {}).get("number", "")
    call_id = call_data.get("id", "")

    handlers = {
        "schedule_appointment": _tool_schedule_appointment,
        "schedule_callback": _tool_schedule_callback,
        "log_call_outcome": _tool_log_call_outcome,
    }

    handler = handlers.get(fn_name)
    if not handler:
        logger.warning("Unknown Vapi function call: %s", fn_name)
        return {"result": f"Unknown function: {fn_name}"}

    try:
        result = await handler(params, customer_number, call_id)
        return {"result": result}
    except Exception:
        logger.exception("Error handling Vapi tool call %s", fn_name)
        return {"result": f"Error processing {fn_name}. The appointment team has been notified."}


# ── Tool Handlers ──────────────────────────────────────────────────────


async def _tool_schedule_appointment(
    params: dict, customer_number: str, call_id: str
) -> str:
    """Create an appointment and update lead status."""
    async with AsyncSession(async_engine) as db:
        lead = await _find_lead_by_phone(db, customer_number)
        if not lead:
            return "I couldn't find your account — our team will follow up to confirm the appointment."

        rep = await _get_available_rep(db, lead)
        if not rep:
            return "Appointment noted — a representative will reach out shortly to confirm."

        # Parse date/time
        try:
            date_str = params.get("appointment_date", "")
            time_str = params.get("appointment_time", "")
            start = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            start = start.replace(tzinfo=ET)
            end = start + timedelta(minutes=30)
        except (ValueError, TypeError):
            return "I'll have our scheduling team confirm the exact time with you."

        # Get address from property
        prop = await db.get(Property, lead.property_id)
        address = prop.address_line1 if prop else None

        appt = Appointment(
            lead_id=lead.id,
            rep_id=rep.id,
            status=AppointmentStatus.scheduled,
            scheduled_start=start,
            scheduled_end=end,
            address=address,
            notes=_build_appt_notes(params),
        )
        db.add(appt)

        # Update lead status
        lead.status = LeadStatus.appointment_set
        if not lead.assigned_rep_id:
            lead.assigned_rep_id = rep.id

        # Create outreach attempt record
        attempt = OutreachAttempt(
            lead_id=lead.id,
            channel=ContactChannel.voice,
            disposition=ContactDisposition.appointment_booked,
            external_call_id=call_id,
            qualified=True,
            qualification_data={
                "decision_makers_confirmed": params.get("decision_makers_confirmed"),
                "credit_qualified": params.get("credit_qualified"),
                "utility_bill_confirmed": params.get("utility_bill_confirmed"),
                "agent": "rebecca",
            },
        )
        db.add(attempt)

        db.add(AuditLog(
            actor="vapi:rebecca",
            action="appointment.booked_by_agent",
            entity_type="lead",
            entity_id=lead.id,
            new_value=f"appt={start.isoformat()}, rep={rep.name}",
        ))

        await db.commit()

        return (
            f"Appointment confirmed for {start.strftime('%A, %B %d at %-I:%M %p')} ET. "
            "You'll receive a text confirmation shortly."
        )


async def _tool_schedule_callback(
    params: dict, customer_number: str, call_id: str
) -> str:
    """Record a scheduled callback and update lead for re-contact."""
    async with AsyncSession(async_engine) as db:
        lead = await _find_lead_by_phone(db, customer_number)
        if not lead:
            return "Callback noted — we'll reach out at the time discussed."

        # Parse callback time
        try:
            date_str = params.get("callback_date", "")
            time_str = params.get("callback_time", "")
            callback_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            callback_at = callback_at.replace(tzinfo=ET)
        except (ValueError, TypeError):
            callback_at = datetime.now(ET) + timedelta(hours=4)

        # Update lead for next outreach
        lead.next_outreach_at = callback_at
        lead.next_outreach_channel = ContactChannel.voice
        if lead.status in (LeadStatus.ingested, LeadStatus.scored):
            lead.status = LeadStatus.contacted

        attempt = OutreachAttempt(
            lead_id=lead.id,
            channel=ContactChannel.voice,
            disposition=ContactDisposition.callback_scheduled,
            external_call_id=call_id,
            qualification_data={
                "callback_reason": params.get("reason"),
                "callback_at": callback_at.isoformat(),
                "homeowner_name": params.get("homeowner_name"),
                "notes": params.get("notes"),
                "agent": "rebecca",
            },
        )
        db.add(attempt)

        db.add(AuditLog(
            actor="vapi:rebecca",
            action="callback.scheduled_by_agent",
            entity_type="lead",
            entity_id=lead.id,
            new_value=f"callback={callback_at.isoformat()}, reason={params.get('reason')}",
        ))

        await db.commit()

        return f"Callback scheduled for {callback_at.strftime('%A, %B %d at %-I:%M %p')} ET."


async def _tool_log_call_outcome(
    params: dict, customer_number: str, call_id: str
) -> str:
    """Log the final call disposition."""
    async with AsyncSession(async_engine) as db:
        lead = await _find_lead_by_phone(db, customer_number)

        disposition_raw = params.get("disposition", "completed")
        db_disposition = _DISPOSITION_MAP.get(disposition_raw, ContactDisposition.completed)

        if lead:
            # Update lead status based on disposition
            new_status = _STATUS_MAP.get(disposition_raw)
            if new_status and lead.status not in (
                LeadStatus.appointment_set,
                LeadStatus.closed_won,
            ):
                lead.status = new_status

            # DNC: mark immediately
            if disposition_raw == "dnc":
                lead.status = LeadStatus.dnc

            attempt = OutreachAttempt(
                lead_id=lead.id,
                channel=ContactChannel.voice,
                disposition=db_disposition,
                external_call_id=call_id,
                qualification_data={
                    "homeowner_name": params.get("homeowner_name"),
                    "objections": params.get("objections", []),
                    "interest_level": params.get("interest_level"),
                    "notes": params.get("notes"),
                    "agent": "rebecca",
                },
            )
            db.add(attempt)

            db.add(AuditLog(
                actor="vapi:rebecca",
                action="call.outcome_logged",
                entity_type="lead",
                entity_id=lead.id,
                new_value=disposition_raw,
            ))

            await db.commit()

        return "Call outcome recorded."


def _build_appt_notes(params: dict) -> str:
    """Build appointment notes from tool parameters."""
    parts = []
    if params.get("homeowner_name"):
        parts.append(f"Homeowner: {params['homeowner_name']}")
    if params.get("decision_makers_confirmed"):
        parts.append("Decision-makers confirmed")
    if params.get("credit_qualified"):
        parts.append("Credit ~650+ confirmed")
    if params.get("utility_bill_confirmed"):
        parts.append("Utility bill will be available")
    if params.get("notes"):
        parts.append(f"Notes: {params['notes']}")
    parts.append("Booked by: Rebecca (AI agent)")
    return " | ".join(parts)
