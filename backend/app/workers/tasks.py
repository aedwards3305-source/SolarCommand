"""Celery background tasks for outreach processing."""

import random
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schema import (
    AuditLog,
    ContactChannel,
    ContactDisposition,
    Lead,
    LeadStatus,
    OutreachAttempt,
)
from app.workers.celery_app import celery_app

settings = get_settings()

# Celery tasks use synchronous DB (Celery doesn't support async natively)
sync_engine = create_engine(settings.database_url_sync, echo=False)


@celery_app.task(name="app.workers.tasks.process_outreach_queue")
def process_outreach_queue():
    """Poll for pending outreach attempts and simulate execution.

    In production, this would:
    - For voice: initiate a Twilio call with the AI agent
    - For SMS: send via Twilio SMS API
    - For email: send via SendGrid
    """
    with Session(sync_engine) as db:
        # Find pending attempts (no disposition yet)
        result = db.execute(
            select(OutreachAttempt)
            .where(OutreachAttempt.disposition.is_(None))
            .limit(10)
        )
        attempts = result.scalars().all()

        for attempt in attempts:
            _simulate_outreach(db, attempt)

        db.commit()


@celery_app.task(name="app.workers.tasks.execute_outreach")
def execute_outreach(attempt_id: int):
    """Execute a single outreach attempt."""
    with Session(sync_engine) as db:
        attempt = db.get(OutreachAttempt, attempt_id)
        if not attempt:
            return

        if attempt.disposition is not None:
            return  # Already processed

        _simulate_outreach(db, attempt)
        db.commit()


def _simulate_outreach(db: Session, attempt: OutreachAttempt):
    """Simulate an outreach attempt.

    MVP STUB: Randomly assigns a disposition to test the pipeline.
    Replace with real Twilio/SendGrid integration.
    """
    lead = db.get(Lead, attempt.lead_id)
    if not lead:
        return

    now = datetime.now(tz=timezone.utc)

    if attempt.channel == ContactChannel.voice:
        # Simulate a voice call
        dispositions = [
            (ContactDisposition.appointment_booked, 0.15),
            (ContactDisposition.interested_not_ready, 0.10),
            (ContactDisposition.not_interested, 0.15),
            (ContactDisposition.no_answer, 0.35),
            (ContactDisposition.voicemail, 0.20),
            (ContactDisposition.wrong_number, 0.05),
        ]

        roll = random.random()
        cumulative = 0.0
        chosen = ContactDisposition.no_answer
        for disp, prob in dispositions:
            cumulative += prob
            if roll <= cumulative:
                chosen = disp
                break

        attempt.disposition = chosen
        attempt.ended_at = now
        attempt.duration_seconds = random.randint(5, 180) if chosen != ContactDisposition.no_answer else 0
        attempt.transcript = f"[SIMULATED] Disposition: {chosen.value}"

        lead.total_call_attempts += 1
        lead.last_contacted_at = now

        # Update lead status based on disposition — but never downgrade
        # from appointment_set, qualified, or closed_won
        protected_statuses = {
            LeadStatus.appointment_set,
            LeadStatus.qualified,
            LeadStatus.closed_won,
        }
        if lead.status not in protected_statuses:
            status_map = {
                ContactDisposition.appointment_booked: LeadStatus.qualified,
                ContactDisposition.interested_not_ready: LeadStatus.nurturing,
                ContactDisposition.not_interested: LeadStatus.closed_lost,
                ContactDisposition.no_answer: LeadStatus.contacting,
                ContactDisposition.voicemail: LeadStatus.contacting,
                ContactDisposition.wrong_number: LeadStatus.disqualified,
            }
            lead.status = status_map.get(chosen, LeadStatus.contacting)

    elif attempt.channel == ContactChannel.sms:
        attempt.disposition = ContactDisposition.completed
        attempt.ended_at = now
        attempt.message_body = "[SIMULATED] SMS sent"
        lead.total_sms_sent += 1
        lead.last_contacted_at = now

    elif attempt.channel == ContactChannel.email:
        attempt.disposition = ContactDisposition.completed
        attempt.ended_at = now
        attempt.message_body = "[SIMULATED] Email sent"
        lead.total_emails_sent += 1

    # Audit log
    db.add(
        AuditLog(
            actor="worker",
            action=f"outreach.{attempt.channel.value}.completed",
            entity_type="outreach_attempt",
            entity_id=attempt.id,
            new_value=f"disposition={attempt.disposition.value}" if attempt.disposition else "",
        )
    )
