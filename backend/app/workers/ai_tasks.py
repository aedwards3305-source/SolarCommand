"""Celery tasks for AI modules: SMS, QA, NBA, objections, contact validation, scripts."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.schema import (
    AuditLog,
    ContactChannel,
    ContactIntelligence,
    ConsentLog,
    ConsentStatus,
    ConversationTranscript,
    InboundMessage,
    Lead,
    LeadScore,
    LeadStatus,
    MessageDirection,
    NBAAction,
    NBADecision,
    ObjectionTag,
    OutreachAttempt,
    QAReview,
    ScriptExperiment,
    ScriptVersion,
)
from app.services.ai_client import get_ai_client
from app.services.compliance import handle_opt_out_sync, is_opt_out_message
from app.services.prompts import (
    INSIGHTS_SYSTEM,
    INSIGHTS_USER,
    NBA_SYSTEM,
    NBA_USER,
    OBJECTION_SYSTEM,
    OBJECTION_USER,
    QA_REVIEW_SYSTEM,
    QA_REVIEW_USER,
    SCRIPT_SUGGEST_SYSTEM,
    SCRIPT_SUGGEST_USER,
    SMS_AGENT_SYSTEM,
    SMS_AGENT_USER,
    render_template,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

settings = get_settings()
sync_engine = create_engine(settings.database_url_sync, echo=False)


def _run_async(coro):
    """Run an async coroutine from sync Celery task context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Contact Validation ───────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_validate_contact")
def task_validate_contact(lead_id: int):
    """Validate phone/email for a lead. MVP: basic format checks."""
    with Session(sync_engine) as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        phone_valid = bool(lead.phone and len(lead.phone) >= 10)
        phone_type = "mobile" if phone_valid else None  # MVP assumption

        email_valid = bool(lead.email and "@" in lead.email)

        # Check if record exists
        existing = db.execute(
            select(ContactIntelligence).where(ContactIntelligence.lead_id == lead_id)
        ).scalar_one_or_none()

        if existing:
            existing.phone_valid = phone_valid
            existing.phone_type = phone_type
            existing.email_valid = email_valid
            existing.email_deliverable = email_valid
        else:
            ci = ContactIntelligence(
                lead_id=lead_id,
                phone_valid=phone_valid,
                phone_type=phone_type,
                carrier_name=None,
                email_valid=email_valid,
                email_deliverable=email_valid,
                timezone="America/New_York",
                provider_payload={"source": "mvp_validation"},
            )
            db.add(ci)

        db.add(AuditLog(
            actor="system",
            action="contact.validated",
            entity_type="lead",
            entity_id=lead_id,
            new_value=json.dumps({"phone_valid": phone_valid, "email_valid": email_valid}),
        ))

        db.commit()


# ── Send SMS ─────────────────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_send_sms")
def task_send_sms(lead_id: int, message: str, script_version_id: int | None = None):
    """Send an SMS message. MVP: records the message; real Twilio integration TBD."""
    with Session(sync_engine) as db:
        lead = db.get(Lead, lead_id)
        if not lead or not lead.phone:
            return

        # Check DNC
        if lead.status == LeadStatus.dnc:
            return

        opt_out = db.execute(
            select(ConsentLog)
            .where(ConsentLog.lead_id == lead_id, ConsentLog.status == ConsentStatus.opted_out)
            .limit(1)
        ).scalar_one_or_none()
        if opt_out:
            return

        # Record outbound message
        msg = InboundMessage(
            lead_id=lead_id,
            direction=MessageDirection.outbound,
            channel=ContactChannel.sms,
            from_number=settings.twilio_phone_number or "+10000000000",
            to_number=lead.phone,
            body=message,
            sent_by="ai_agent",
            script_version_id=script_version_id,
        )
        db.add(msg)

        # Update lead tracking
        lead.total_sms_sent += 1
        lead.last_contacted_at = datetime.now(tz=timezone.utc)

        # Create outreach attempt
        attempt = OutreachAttempt(
            lead_id=lead_id,
            channel=ContactChannel.sms,
            message_body=message,
            script_version_id=script_version_id,
        )
        db.add(attempt)

        db.add(AuditLog(
            actor="ai_agent",
            action="sms.sent",
            entity_type="lead",
            entity_id=lead_id,
            new_value=message[:200],
        ))

        db.commit()

        # TODO: In production, call Twilio API here:
        # twilio_client.messages.create(to=lead.phone, from_=settings.twilio_phone_number, body=message)


# ── Process Inbound SMS ──────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_process_inbound_sms")
def task_process_inbound_sms(message_id: int):
    """Process an inbound SMS: classify intent, handle opt-out, generate reply."""
    with Session(sync_engine) as db:
        msg = db.get(InboundMessage, message_id)
        if not msg:
            return

        lead = db.get(Lead, msg.lead_id)
        if not lead:
            return

        # 1. Check for opt-out FIRST (deterministic, no AI needed)
        if is_opt_out_message(msg.body):
            msg.ai_intent = "opt_out"
            msg.ai_actions = [{"action": "opt_out"}]
            handle_opt_out_sync(db, lead, msg.body, "sms")

            # Send opt-out confirmation
            confirm = InboundMessage(
                lead_id=lead.id,
                direction=MessageDirection.outbound,
                channel=ContactChannel.sms,
                from_number=settings.twilio_phone_number or "+10000000000",
                to_number=msg.from_number,
                body="You have been unsubscribed and will not receive further messages. Reply HELP for assistance.",
                sent_by="system",
            )
            db.add(confirm)
            db.commit()
            return

        # 2. AI classification
        ai = get_ai_client()

        # Get latest score
        score_row = db.execute(
            select(LeadScore.total_score)
            .where(LeadScore.lead_id == lead.id)
            .order_by(LeadScore.scored_at.desc())
            .limit(1)
        ).scalar()

        # Count previous messages
        msg_count = db.execute(
            select(func.count(InboundMessage.id))
            .where(InboundMessage.lead_id == lead.id)
        ).scalar() or 0

        system_prompt = render_template(
            SMS_AGENT_SYSTEM,
            company_name="SolarCommand",
            address=f"{lead.first_name or ''} {lead.last_name or ''}'s property",
        )
        user_prompt = render_template(
            SMS_AGENT_USER,
            lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Homeowner",
            lead_status=lead.status.value,
            lead_score=str(score_row or "N/A"),
            address="on file",
            county="",
            message_count=str(msg_count),
            from_number=msg.from_number or "",
            message_body=msg.body,
        )

        result = _run_async(ai.chat(system_prompt, user_prompt))

        msg.ai_intent = result.get("intent", "unknown")
        msg.ai_suggested_reply = result.get("reply_text", "")
        msg.ai_actions = result.get("actions", [])
        msg.ai_model = ai.model if ai.enabled else "fallback"

        # 3. Process actions
        for action in result.get("actions", []):
            act = action.get("action", "")
            if act == "opt_out":
                handle_opt_out_sync(db, lead, msg.body, "sms")
            elif act == "book_appointment":
                # Flag for rep — don't auto-book
                lead.status = LeadStatus.qualified
                db.add(AuditLog(
                    actor="ai_agent",
                    action="lead.qualified_by_sms",
                    entity_type="lead",
                    entity_id=lead.id,
                    new_value="qualified",
                ))
            elif act == "rep_handoff":
                db.add(AuditLog(
                    actor="ai_agent",
                    action="lead.rep_handoff_requested",
                    entity_type="lead",
                    entity_id=lead.id,
                    metadata_json={"reason": "AI flagged for human review"},
                ))

        # 4. Auto-send reply if enabled
        if settings.sms_auto_reply_enabled and msg.ai_suggested_reply:
            if not result.get("requires_human", True):
                reply = InboundMessage(
                    lead_id=lead.id,
                    direction=MessageDirection.outbound,
                    channel=ContactChannel.sms,
                    from_number=settings.twilio_phone_number or "+10000000000",
                    to_number=msg.from_number,
                    body=msg.ai_suggested_reply,
                    sent_by="ai_agent",
                    ai_model=msg.ai_model,
                )
                db.add(reply)

        db.commit()


# ── Transcript Summary ───────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_generate_transcript_summary")
def task_generate_transcript_summary(conversation_id: int):
    """Generate AI summary for a conversation transcript."""
    with Session(sync_engine) as db:
        convo = db.get(ConversationTranscript, conversation_id)
        if not convo or not convo.raw_transcript:
            return

        ai = get_ai_client()
        result = _run_async(ai.chat(
            "You are a conversation summarizer. Summarize this solar outreach conversation in 2-3 sentences. "
            "Include: customer sentiment, key topics discussed, and outcome. "
            "Also classify sentiment as positive, neutral, or negative. "
            "Respond with JSON: {\"summary\": \"...\", \"sentiment\": \"positive|neutral|negative\"}",
            f"Transcript:\n{convo.raw_transcript}",
        ))

        convo.ai_summary = result.get("summary", "")
        convo.ai_sentiment = result.get("sentiment", "neutral")
        convo.ai_output = result
        convo.ai_model = ai.model if ai.enabled else "fallback"

        db.commit()


# ── QA Review ────────────────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_run_qa_review")
def task_run_qa_review(conversation_id: int):
    """Run QA compliance review on a conversation."""
    with Session(sync_engine) as db:
        convo = db.get(ConversationTranscript, conversation_id)
        if not convo:
            return

        lead = db.get(Lead, convo.lead_id)

        ai = get_ai_client()
        system_prompt = QA_REVIEW_SYSTEM
        user_prompt = render_template(
            QA_REVIEW_USER,
            channel=convo.channel.value if convo.channel else "sms",
            lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() if lead else "Unknown",
            lead_id=str(convo.lead_id),
            timestamp=convo.created_at.isoformat() if convo.created_at else "",
            transcript=convo.raw_transcript,
        )

        result = _run_async(ai.chat(system_prompt, user_prompt))

        review = QAReview(
            lead_id=convo.lead_id,
            conversation_id=conversation_id,
            compliance_score=result.get("compliance_score", 70),
            flags=result.get("flags", []),
            checklist_pass=result.get("checklist_pass", True),
            rationale=result.get("rationale", ""),
            reviewed_by="ai_agent",
            ai_output=result,
            ai_model=ai.model if ai.enabled else "fallback",
        )
        db.add(review)

        # Audit if critical flags
        flags = result.get("flags", [])
        critical = [f for f in flags if isinstance(f, dict) and f.get("severity") == "critical"]
        if critical:
            db.add(AuditLog(
                actor="ai_agent",
                action="qa.critical_flag",
                entity_type="lead",
                entity_id=convo.lead_id,
                new_value=json.dumps(critical[:3]),
                metadata_json={"conversation_id": conversation_id},
            ))

        db.commit()
        return review.id


# ── Objection Extraction ─────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_extract_objections")
def task_extract_objections(conversation_id: int):
    """Extract objection tags from a conversation transcript."""
    with Session(sync_engine) as db:
        convo = db.get(ConversationTranscript, conversation_id)
        if not convo:
            return

        ai = get_ai_client()
        system_prompt = OBJECTION_SYSTEM
        user_prompt = render_template(OBJECTION_USER, transcript=convo.raw_transcript)

        result = _run_async(ai.chat(system_prompt, user_prompt))

        tags = result.get("tags", [])
        for tag_data in tags:
            if not isinstance(tag_data, dict):
                continue
            tag = ObjectionTag(
                conversation_id=conversation_id,
                lead_id=convo.lead_id,
                tag=tag_data.get("tag", "unknown"),
                confidence=tag_data.get("confidence", 0.0),
                evidence_span=tag_data.get("evidence_span", ""),
                ai_output=tag_data,
            )
            db.add(tag)

        db.commit()


# ── NBA Decision ─────────────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_nba_decide")
def task_nba_decide(lead_id: int):
    """Compute next-best-action for a lead."""
    with Session(sync_engine) as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return

        # Stop conditions
        terminal = {
            LeadStatus.closed_won, LeadStatus.closed_lost,
            LeadStatus.dnc, LeadStatus.archived, LeadStatus.disqualified,
        }
        if lead.status in terminal:
            decision = NBADecision(
                lead_id=lead_id,
                recommended_action=NBAAction.close,
                reason_codes=["terminal_status"],
                confidence=1.0,
                expires_at=datetime.now(tz=timezone.utc) + timedelta(days=30),
            )
            db.add(decision)
            db.commit()
            return

        # Protected statuses → rep_handoff
        protected = {LeadStatus.appointment_set, LeadStatus.qualified}
        if lead.status in protected:
            decision = NBADecision(
                lead_id=lead_id,
                recommended_action=NBAAction.rep_handoff,
                reason_codes=["protected_status"],
                confidence=0.9,
                expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
            )
            db.add(decision)
            db.commit()
            return

        # Get contact intelligence
        ci = db.execute(
            select(ContactIntelligence).where(ContactIntelligence.lead_id == lead_id)
        ).scalar_one_or_none()

        # Get latest score
        score = db.execute(
            select(LeadScore.total_score)
            .where(LeadScore.lead_id == lead_id)
            .order_by(LeadScore.scored_at.desc())
            .limit(1)
        ).scalar() or 0

        # Check DNC
        is_dnc = db.execute(
            select(ConsentLog)
            .where(ConsentLog.lead_id == lead_id, ConsentLog.status == ConsentStatus.opted_out)
            .limit(1)
        ).scalar_one_or_none() is not None

        if is_dnc:
            decision = NBADecision(
                lead_id=lead_id,
                recommended_action=NBAAction.close,
                reason_codes=["opted_out"],
                confidence=1.0,
                expires_at=datetime.now(tz=timezone.utc) + timedelta(days=30),
            )
            db.add(decision)
            db.commit()
            return

        now = datetime.now(tz=timezone.utc)
        et_hour = (now.hour - 5) % 24

        ai = get_ai_client()
        system_prompt = NBA_SYSTEM
        user_prompt = render_template(
            NBA_USER,
            lead_id=str(lead_id),
            lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Unknown",
            lead_status=lead.status.value,
            lead_score=str(score),
            phone_type=ci.phone_type if ci else "unknown",
            best_call_hour=str(ci.best_call_hour if ci and ci.best_call_hour else "N/A"),
            call_attempts=str(lead.total_call_attempts),
            sms_sent=str(lead.total_sms_sent),
            emails_sent=str(lead.total_emails_sent),
            last_contacted=lead.last_contacted_at.isoformat() if lead.last_contacted_at else "never",
            is_dnc="no",
            consent_status="opted_in",
            current_time_et=f"{et_hour}:00",
        )

        result = _run_async(ai.chat(system_prompt, user_prompt))

        # Map action string to enum
        action_map = {
            "call": NBAAction.call, "sms": NBAAction.sms, "email": NBAAction.email,
            "wait": NBAAction.wait, "rep_handoff": NBAAction.rep_handoff,
            "nurture": NBAAction.nurture, "close": NBAAction.close,
        }
        action = action_map.get(result.get("next_action", "wait"), NBAAction.wait)

        channel_map = {
            "voice": ContactChannel.voice, "sms": ContactChannel.sms,
            "email": ContactChannel.email,
        }
        channel = channel_map.get(result.get("channel")) if result.get("channel") else None

        decision = NBADecision(
            lead_id=lead_id,
            recommended_action=action,
            recommended_channel=channel,
            reason_codes=result.get("reason_codes", []),
            confidence=result.get("confidence", 0.0),
            ai_output=result,
            ai_model=ai.model if ai.enabled else "fallback",
            expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
        )
        db.add(decision)
        db.commit()


# ── Script Suggestion ────────────────────────────────────────────────────


@celery_app.task(name="app.workers.ai_tasks.task_script_suggest")
def task_script_suggest(channel: str, script_version_id: int, dataset_window_days: int = 30):
    """Generate AI-suggested script revision."""
    with Session(sync_engine) as db:
        script = db.get(ScriptVersion, script_version_id)
        if not script:
            return {}

        # Get objection patterns from recent conversations
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=dataset_window_days)
        objections = db.execute(
            select(ObjectionTag.tag, func.count(ObjectionTag.id).label("cnt"))
            .where(ObjectionTag.created_at >= cutoff)
            .group_by(ObjectionTag.tag)
            .order_by(func.count(ObjectionTag.id).desc())
            .limit(10)
        ).all()

        objection_summary = ", ".join(f"{t} ({c}x)" for t, c in objections) or "No data yet"
        top_objections = ", ".join(t for t, _ in objections[:5]) or "None"

        ai = get_ai_client()
        system_prompt = SCRIPT_SUGGEST_SYSTEM
        user_prompt = render_template(
            SCRIPT_SUGGEST_USER,
            channel=channel,
            version_label=script.version_label,
            script_content=script.content or "",
            window_days=str(dataset_window_days),
            objection_summary=objection_summary,
            response_rate="N/A",
            conversion_rate="N/A",
            top_objections=top_objections,
        )

        result = _run_async(ai.chat(system_prompt, user_prompt))
        return result
