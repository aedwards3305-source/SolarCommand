"""SMS service — send text messages via Twilio.

Works standalone (no Celery/Redis required). Can be called from
FastAPI endpoints directly or from Celery tasks.
"""

import logging
import re

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def normalize_phone(raw: str) -> str | None:
    """Normalize a US phone number to E.164 format (+1XXXXXXXXXX).

    Accepts: 9072022558, (907)202-2558, 907-202-2558, +19072022558, etc.
    Returns None if the input can't be parsed into 10 digits.
    """
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return None
    return f"+1{digits}"


def send_sms(to: str, body: str, from_: str | None = None) -> dict:
    """Send an SMS via Twilio. Returns {"sid": ..., "status": ...} or {"error": ...}.

    Non-blocking in the sense that failures are caught and logged,
    never raising to the caller. Safe to call from async endpoints
    via asyncio.to_thread() or directly from sync Celery tasks.
    """
    settings = get_settings()

    if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_phone_number]):
        logger.warning("Twilio not configured — SMS not sent to %s", to)
        return {"error": "twilio_not_configured"}

    to_e164 = normalize_phone(to)
    if not to_e164:
        logger.warning("Invalid phone number: %s", to)
        return {"error": "invalid_phone", "raw": to}

    from_number = from_ or settings.twilio_phone_number

    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        message = client.messages.create(
            to=to_e164,
            from_=from_number,
            body=body,
        )
        logger.info("SMS sent to %s (SID=%s, status=%s)", to_e164, message.sid, message.status)
        return {"sid": message.sid, "status": message.status}
    except Exception as e:
        logger.error("Twilio SMS send failed to %s: %s", to_e164, e)
        return {"error": str(e)}


async def send_sms_async(to: str, body: str, from_: str | None = None) -> dict:
    """Async wrapper around send_sms — safe to call from FastAPI endpoints."""
    import asyncio
    return await asyncio.to_thread(send_sms, to, body, from_)


# ── SMS Templates ────────────────────────────────────────────────────────


def quote_confirmation_sms(first_name: str) -> str:
    """SMS sent immediately after a customer submits a quote request."""
    return (
        f"Hi {first_name}! Thanks for requesting a free solar quote from Solar Command. "
        f"We'll review your info and reach out within 24 hours. "
        f"Questions? Call or text us at (301) 364-3492. "
        f"— Solar Command | MHIC #165263"
    )


def appointment_confirmation_sms(first_name: str, date_str: str, time_pref: str) -> str:
    """SMS sent after a customer schedules a consultation."""
    return (
        f"Hi {first_name}! Your free solar consultation is confirmed for "
        f"{date_str} ({time_pref}). We'll text you a reminder beforehand. "
        f"Need to reschedule? Reply to this text or call (301) 364-3492. "
        f"— Solar Command"
    )


def initial_outreach_sms(first_name: str, address: str) -> str:
    """First outreach SMS to a new lead (from CRM or auto-triggered)."""
    settings = get_settings()
    scheduling_url = settings.scheduling_url or "https://solarcommandtech.com/get-quote"
    return (
        f"Hi {first_name}, this is Steffen from Solar Command! "
        f"I noticed your home at {address} could be a great fit for solar. "
        f"Maryland homeowners are saving $150+/mo with $0 down and the 30% federal tax credit. "
        f"Want to see your savings? Book a free consultation: {scheduling_url} "
        f"— Solar Command | MHIC #165263"
    )


def followup_1_sms(first_name: str) -> str:
    """Follow-up SMS #1 — sent ~24 hours after initial outreach with no response."""
    settings = get_settings()
    scheduling_url = settings.scheduling_url or "https://solarcommandtech.com/get-quote"
    return (
        f"Hey {first_name}, just following up from Solar Command. "
        f"Maryland's 30% federal tax credit + local incentives won't last forever. "
        f"We offer a free no-pressure consultation — takes about 15 minutes. "
        f"Grab a time here: {scheduling_url} "
        f"Reply STOP to opt out."
    )


def followup_2_sms(first_name: str) -> str:
    """Follow-up SMS #2 — sent ~72 hours after initial outreach with no response."""
    return (
        f"Hi {first_name}, last check-in from Solar Command. "
        f"Your neighbors are going solar and locking in savings before rates rise. "
        f"If now isn't the right time, no worries — just reply and let me know. "
        f"Otherwise, call or text me anytime at (301) 364-3492. — Steffen"
    )
