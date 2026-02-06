"""Outreach orchestration — scheduling, channel selection, compliance gates."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.schema import (
    ConsentLog,
    ConsentStatus,
    ContactChannel,
    Lead,
    LeadStatus,
    OutreachAttempt,
)

MAX_CALL_ATTEMPTS = 3
MAX_SMS_ATTEMPTS = 3
MAX_EMAIL_ATTEMPTS = 5


async def check_dnc(db: AsyncSession, lead: Lead) -> bool:
    """Return True if the lead is on the Do Not Call list (internal)."""
    result = await db.execute(
        select(ConsentLog)
        .where(ConsentLog.lead_id == lead.id)
        .where(ConsentLog.status == ConsentStatus.opted_out)
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


def is_within_call_window() -> bool:
    """Check if current Eastern Time is within allowed call hours."""
    settings = get_settings()
    # Simplified: assumes server is in ET or use pytz for production
    now = datetime.now(tz=timezone.utc)
    # ET is UTC-5 (EST) or UTC-4 (EDT) — use UTC-5 as conservative default
    et_hour = (now.hour - 5) % 24
    weekday = now.weekday()  # 0=Mon, 6=Sun

    if weekday == 6:  # Sunday — no calls
        return False
    if weekday == 5:  # Saturday 10-17
        return 10 <= et_hour < 17
    # Mon-Fri
    return settings.call_start_hour <= et_hour < settings.call_end_hour


def is_within_sms_window() -> bool:
    """Check if current Eastern Time is within allowed SMS hours."""
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    et_hour = (now.hour - 5) % 24
    weekday = now.weekday()

    if weekday == 6:  # Sunday — no SMS
        return False
    return settings.sms_start_hour <= et_hour < settings.sms_end_hour


async def can_contact(db: AsyncSession, lead: Lead) -> tuple[bool, str]:
    """Run all pre-contact compliance checks. Returns (allowed, reason)."""
    # Check DNC
    if await check_dnc(db, lead):
        return False, "Lead is on DNC / opted out"

    # Check lead status
    blocked_statuses = {
        LeadStatus.dnc,
        LeadStatus.disqualified,
        LeadStatus.closed_won,
        LeadStatus.closed_lost,
        LeadStatus.archived,
    }
    if lead.status in blocked_statuses:
        return False, f"Lead status is {lead.status.value}"

    # Check max attempts
    if lead.total_call_attempts >= MAX_CALL_ATTEMPTS and \
       lead.total_sms_sent >= MAX_SMS_ATTEMPTS and \
       lead.total_emails_sent >= MAX_EMAIL_ATTEMPTS:
        return False, "All channel attempt limits exhausted"

    return True, "OK"


def select_channel(lead: Lead) -> ContactChannel | None:
    """Pick the next outreach channel based on escalation logic."""
    # Call first if under limit and in window
    if lead.total_call_attempts < MAX_CALL_ATTEMPTS:
        if is_within_call_window():
            return ContactChannel.voice
        elif lead.total_sms_sent < MAX_SMS_ATTEMPTS and is_within_sms_window():
            return ContactChannel.sms
        else:
            return None  # Defer until window opens

    # Escalate to SMS
    if lead.total_sms_sent < MAX_SMS_ATTEMPTS:
        if is_within_sms_window():
            return ContactChannel.sms
        return None

    # Escalate to email
    if lead.total_emails_sent < MAX_EMAIL_ATTEMPTS:
        return ContactChannel.email

    return None  # Exhausted


async def enqueue_outreach(db: AsyncSession, lead_id: int) -> OutreachAttempt | None:
    """Create an outreach attempt record for the next channel."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} not found")

    allowed, reason = await can_contact(db, lead)
    if not allowed:
        return None

    channel = select_channel(lead)
    if channel is None:
        return None

    attempt = OutreachAttempt(
        lead_id=lead.id,
        channel=channel,
    )
    db.add(attempt)

    # Update lead tracking
    lead.status = LeadStatus.contacting
    lead.next_outreach_channel = channel

    await db.flush()
    return attempt
