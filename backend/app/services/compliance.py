"""Compliance and safety logic — opt-out, DNC, quiet hours, consent."""

import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schema import (
    AuditLog,
    ConsentLog,
    ConsentStatus,
    ConsentType,
    ContactChannel,
    Lead,
    LeadStatus,
)

# Opt-out keywords (case-insensitive, exact match or contained in message)
OPT_OUT_KEYWORDS = {
    "stop", "unsubscribe", "cancel", "end", "quit",
    "opt out", "optout", "opt-out", "remove me", "do not contact",
    "don't contact", "leave me alone",
}

# Compiled pattern for efficiency
_OPT_OUT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in OPT_OUT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def is_opt_out_message(text: str) -> bool:
    """Check if message text contains opt-out keywords."""
    return bool(_OPT_OUT_PATTERN.search(text))


def is_within_quiet_hours(tz_name: str = "America/New_York") -> bool:
    """Check if current time is within allowed outreach hours.

    Default: 9am-9pm ET, Mon-Sat. No Sunday.
    Uses a simplified UTC offset approach (UTC-5 for EST).
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    # Simplified ET offset: UTC-5 (conservative, ignores DST for safety)
    et_hour = (now.hour - 5) % 24
    weekday = now.weekday()  # 0=Mon, 6=Sun

    if weekday == 6:  # Sunday — no contact
        return False
    if weekday == 5:  # Saturday 10am-5pm
        return 10 <= et_hour < 17

    # Mon-Fri
    return settings.sms_start_hour <= et_hour < settings.sms_end_hour


async def handle_opt_out(db: AsyncSession, lead: Lead, message_body: str, channel: str) -> None:
    """Process an opt-out: update consent, update lead status, log audit."""
    # Record consent opt-out
    consent = ConsentLog(
        lead_id=lead.id,
        consent_type=ConsentType.all_channels,
        status=ConsentStatus.opted_out,
        channel=ContactChannel(channel),
        evidence_type="sms_reply",
    )
    db.add(consent)

    # Update lead status to DNC
    old_status = lead.status.value
    lead.status = LeadStatus.dnc

    # Audit log
    db.add(AuditLog(
        actor="ai_agent",
        action="consent.opt_out",
        entity_type="lead",
        entity_id=lead.id,
        old_value=old_status,
        new_value="dnc",
        metadata_json={"trigger": "sms_opt_out", "message": message_body[:200]},
    ))

    await db.flush()


def handle_opt_out_sync(db: Session, lead: Lead, message_body: str, channel: str) -> None:
    """Synchronous version for Celery tasks."""
    consent = ConsentLog(
        lead_id=lead.id,
        consent_type=ConsentType.all_channels,
        status=ConsentStatus.opted_out,
        channel=ContactChannel(channel),
        evidence_type="sms_reply",
    )
    db.add(consent)

    old_status = lead.status.value
    lead.status = LeadStatus.dnc

    db.add(AuditLog(
        actor="ai_agent",
        action="consent.opt_out",
        entity_type="lead",
        entity_id=lead.id,
        old_value=old_status,
        new_value="dnc",
        metadata_json={"trigger": "sms_opt_out", "message": message_body[:200]},
    ))


async def check_can_message(db: AsyncSession, lead: Lead) -> tuple[bool, str]:
    """Check if we can send a message to this lead."""
    # Check DNC status
    if lead.status == LeadStatus.dnc:
        return False, "Lead is on DNC list"

    # Check for opt-out consent
    result = await db.execute(
        select(ConsentLog)
        .where(ConsentLog.lead_id == lead.id)
        .where(ConsentLog.status == ConsentStatus.opted_out)
        .limit(1)
    )
    if result.scalar_one_or_none():
        return False, "Lead has opted out"

    # Check quiet hours
    if not is_within_quiet_hours():
        return False, "Outside allowed contact hours"

    # Check terminal statuses
    terminal = {LeadStatus.closed_won, LeadStatus.closed_lost, LeadStatus.archived}
    if lead.status in terminal:
        return False, f"Lead is in terminal status: {lead.status.value}"

    return True, "OK"
