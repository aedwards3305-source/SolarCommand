"""AI Operator task functions — called by Celery tasks or API routes.

Each function calls Claude, persists the ai_run record, and returns structured output.
All functions are sync (use _run_async for the async Claude client).
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.client import get_claude_client
from app.ai.prompts import (
    INSIGHTS_SYSTEM,
    INSIGHTS_USER,
    MEMORY_SYSTEM,
    MEMORY_USER,
    NBA_SYSTEM,
    NBA_USER,
    OBJECTION_SYSTEM,
    OBJECTION_USER,
    QA_REVIEW_SYSTEM,
    QA_REVIEW_USER,
    REP_BRIEF_SYSTEM,
    REP_BRIEF_USER,
    SCRIPT_SUGGEST_SYSTEM,
    SCRIPT_SUGGEST_USER,
    SMS_AGENT_SYSTEM,
    SMS_AGENT_USER,
    render,
)
from app.ai.storage import get_memories_by_scope_sync, save_ai_run_sync, upsert_memory_sync
from app.models.schema import (
    AIMemory,
    Appointment,
    AppointmentStatus,
    ConsentLog,
    ConsentStatus,
    ContactIntelligence,
    ConversationTranscript,
    InboundMessage,
    Lead,
    LeadScore,
    LeadStatus,
    NBAAction,
    NBADecision,
    ObjectionTag,
    OutreachAttempt,
    QAReview,
    ScriptExperiment,
    ScriptVersion,
    ContactChannel,
)

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _build_memory_context(db: Session, scopes: list[str]) -> str:
    """Build a memory context string for injection into prompts (RAG)."""
    memories = []
    for scope in scopes:
        mems = get_memories_by_scope_sync(db, scope, limit=5)
        for m in mems:
            memories.append(f"[{scope}/{m['key']}] {m['content']}")
    if not memories:
        return ""
    return "Organizational memory (use these insights to improve your response):\n" + "\n".join(memories)


# ── SMS Classification ───────────────────────────────────────────────────


def run_sms_classification(db: Session, message_id: int) -> dict:
    """Classify an inbound SMS and generate a suggested reply."""
    msg = db.get(InboundMessage, message_id)
    if not msg:
        return {}
    lead = db.get(Lead, msg.lead_id)
    if not lead:
        return {}

    score_row = db.execute(
        select(LeadScore.total_score)
        .where(LeadScore.lead_id == lead.id)
        .order_by(LeadScore.scored_at.desc())
        .limit(1)
    ).scalar()

    msg_count = db.execute(
        select(func.count(InboundMessage.id))
        .where(InboundMessage.lead_id == lead.id)
    ).scalar() or 0

    memory_ctx = _build_memory_context(db, ["global", "county:" + (lead.property.county if lead.property else "")])

    system_prompt = render(
        SMS_AGENT_SYSTEM,
        company_name="SolarCommand",
        address=f"{lead.first_name or ''} {lead.last_name or ''}'s property",
        memory_context=memory_ctx,
    )
    user_prompt = render(
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

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="sms_classification",
        lead_id=lead.id,
    ))

    save_ai_run_sync(db, result)
    return result


# ── QA Review ────────────────────────────────────────────────────────────


def run_qa_review(db: Session, conversation_id: int) -> dict:
    """Run QA compliance review on a conversation."""
    convo = db.get(ConversationTranscript, conversation_id)
    if not convo:
        return {}
    lead = db.get(Lead, convo.lead_id)

    system_prompt = QA_REVIEW_SYSTEM
    user_prompt = render(
        QA_REVIEW_USER,
        channel=convo.channel.value if convo.channel else "sms",
        lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() if lead else "Unknown",
        lead_id=str(convo.lead_id),
        timestamp=convo.created_at.isoformat() if convo.created_at else "",
        transcript=convo.raw_transcript,
    )

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="qa_review",
        lead_id=convo.lead_id,
        conversation_id=conversation_id,
    ))

    save_ai_run_sync(db, result)
    return result


# ── Objection Extraction ─────────────────────────────────────────────────


def run_objection_extraction(db: Session, conversation_id: int) -> dict:
    """Extract objection tags from a conversation."""
    convo = db.get(ConversationTranscript, conversation_id)
    if not convo:
        return {}

    system_prompt = OBJECTION_SYSTEM
    user_prompt = render(OBJECTION_USER, transcript=convo.raw_transcript)

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="objection_tags",
        lead_id=convo.lead_id,
        conversation_id=conversation_id,
    ))

    save_ai_run_sync(db, result)
    return result


# ── NBA Decision ─────────────────────────────────────────────────────────


def run_nba(db: Session, lead_id: int) -> dict:
    """Compute next-best-action. Rules first (deterministic), then Claude reasoning."""
    lead = db.get(Lead, lead_id)
    if not lead:
        return {}

    # Hard stop: terminal statuses
    terminal = {LeadStatus.closed_won, LeadStatus.closed_lost, LeadStatus.dnc, LeadStatus.archived, LeadStatus.disqualified}
    if lead.status in terminal:
        return {"next_action": "close", "channel": None, "reason_codes": ["terminal_status"], "confidence": 1.0}

    # Hard stop: opted out
    is_dnc = db.execute(
        select(ConsentLog)
        .where(ConsentLog.lead_id == lead_id, ConsentLog.status == ConsentStatus.opted_out)
        .limit(1)
    ).scalar_one_or_none() is not None
    if is_dnc:
        return {"next_action": "close", "channel": None, "reason_codes": ["opted_out"], "confidence": 1.0}

    # Protected: qualified/appointment_set → rep_handoff
    protected = {LeadStatus.appointment_set, LeadStatus.qualified}
    if lead.status in protected:
        return {"next_action": "rep_handoff", "channel": None, "reason_codes": ["protected_status"], "confidence": 0.9}

    # Get enrichment data
    ci = db.execute(
        select(ContactIntelligence).where(ContactIntelligence.lead_id == lead_id)
    ).scalar_one_or_none()
    score = db.execute(
        select(LeadScore.total_score)
        .where(LeadScore.lead_id == lead_id)
        .order_by(LeadScore.scored_at.desc())
        .limit(1)
    ).scalar() or 0

    now = datetime.now(tz=timezone.utc)
    now_et = now.astimezone(ZoneInfo("America/New_York"))
    et_hour = now_et.hour

    memory_ctx = _build_memory_context(db, ["global"])

    system_prompt = render(NBA_SYSTEM, memory_context=memory_ctx)
    user_prompt = render(
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

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="nba",
        lead_id=lead_id,
    ))

    save_ai_run_sync(db, result)
    return result


# ── Rep Brief ────────────────────────────────────────────────────────────


def run_rep_brief(db: Session, lead_id: int) -> dict:
    """Generate an AI brief for a rep about to contact a lead."""
    lead = db.get(Lead, lead_id)
    if not lead:
        return {}

    prop = lead.property
    score = db.execute(
        select(LeadScore.total_score)
        .where(LeadScore.lead_id == lead_id)
        .order_by(LeadScore.scored_at.desc())
        .limit(1)
    ).scalar() or 0

    # Get recent objections
    objections = db.execute(
        select(ObjectionTag.tag)
        .where(ObjectionTag.lead_id == lead_id)
        .order_by(ObjectionTag.created_at.desc())
        .limit(10)
    ).scalars().all()
    objection_str = ", ".join(objections) if objections else "None detected"

    # Get recent messages
    messages = db.execute(
        select(InboundMessage)
        .where(InboundMessage.lead_id == lead_id)
        .order_by(InboundMessage.created_at.desc())
        .limit(5)
    ).scalars().all()
    msg_str = "\n".join(
        f"[{m.direction.value}] {m.body[:100]}" for m in reversed(list(messages))
    ) or "No messages yet"

    memory_ctx = _build_memory_context(db, ["global", "county:" + (prop.county if prop else "")])

    system_prompt = render(REP_BRIEF_SYSTEM, memory_context=memory_ctx)
    user_prompt = render(
        REP_BRIEF_USER,
        lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "Unknown",
        lead_id=str(lead_id),
        lead_status=lead.status.value,
        lead_score=str(score),
        address=prop.address_line1 if prop else "N/A",
        county=prop.county if prop else "N/A",
        state=prop.state if prop else "MD",
        zip=prop.zip_code if prop else "N/A",
        property_type=prop.property_type.value if prop else "N/A",
        year_built=str(prop.year_built or "N/A") if prop else "N/A",
        roof_area=str(int(prop.roof_area_sqft)) if prop and prop.roof_area_sqft else "N/A",
        assessed_value=f"{int(prop.assessed_value):,}" if prop and prop.assessed_value else "N/A",
        utility_zone=prop.utility_zone if prop else "N/A",
        existing_solar="Yes" if prop and prop.has_existing_solar else "No",
        call_attempts=str(lead.total_call_attempts),
        sms_sent=str(lead.total_sms_sent),
        emails_sent=str(lead.total_emails_sent),
        last_contacted=lead.last_contacted_at.isoformat() if lead.last_contacted_at else "Never",
        objections=objection_str,
        recent_messages=msg_str,
    )

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="rep_brief",
        lead_id=lead_id,
    ))

    save_ai_run_sync(db, result)
    return result


# ── Script Suggestion ────────────────────────────────────────────────────


def run_script_suggest(db: Session, channel: str, script_version_id: int, window_days: int = 30) -> dict:
    """Generate AI-suggested script revision."""
    script = db.get(ScriptVersion, script_version_id)
    if not script:
        return {}

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=window_days)
    objections = db.execute(
        select(ObjectionTag.tag, func.count(ObjectionTag.id).label("cnt"))
        .where(ObjectionTag.created_at >= cutoff)
        .group_by(ObjectionTag.tag)
        .order_by(func.count(ObjectionTag.id).desc())
        .limit(10)
    ).all()

    objection_summary = ", ".join(f"{t} ({c}x)" for t, c in objections) or "No data yet"
    top_objections = ", ".join(t for t, _ in objections[:5]) or "None"

    memory_ctx = _build_memory_context(db, ["global", "script"])

    system_prompt = render(SCRIPT_SUGGEST_SYSTEM, memory_context=memory_ctx)
    user_prompt = render(
        SCRIPT_SUGGEST_USER,
        channel=channel,
        version_label=script.version_label,
        script_content=script.content or "",
        window_days=str(window_days),
        objection_summary=objection_summary,
        response_rate="N/A",
        conversion_rate="N/A",
        top_objections=top_objections,
    )

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="script_suggest",
    ))

    save_ai_run_sync(db, result)
    return result


# ── Weekly Insights ──────────────────────────────────────────────────────


def run_weekly_insights(db: Session) -> dict:
    """Generate weekly AI narrative from aggregated KPIs."""
    now = datetime.now(tz=timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    # Count leads
    total_leads = db.execute(select(func.count(Lead.id))).scalar() or 0
    hot_leads = db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.hot)
    ).scalar() or 0

    leads_this_week = db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= week_ago)
    ).scalar() or 0
    leads_last_week = db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= two_weeks_ago, Lead.created_at < week_ago)
    ).scalar() or 0
    leads_delta = leads_this_week - leads_last_week

    # Appointments
    appts = db.execute(
        select(func.count(Appointment.id))
        .where(Appointment.created_at >= week_ago, Appointment.status != AppointmentStatus.cancelled)
    ).scalar() or 0

    # Avg score
    avg_score = db.execute(select(func.avg(LeadScore.total_score))).scalar()
    avg_score = round(avg_score or 0, 1)

    # Top objections
    objections = db.execute(
        select(ObjectionTag.tag, func.count(ObjectionTag.id))
        .where(ObjectionTag.created_at >= week_ago)
        .group_by(ObjectionTag.tag)
        .order_by(func.count(ObjectionTag.id).desc())
        .limit(5)
    ).all()
    top_objections = ", ".join(f"{t} ({c})" for t, c in objections) or "None"

    # QA avg
    qa_avg = db.execute(
        select(func.avg(QAReview.compliance_score)).where(QAReview.created_at >= week_ago)
    ).scalar()
    qa_avg = round(qa_avg or 0, 1)

    memory_ctx = _build_memory_context(db, ["global"])

    system_prompt = render(INSIGHTS_SYSTEM, memory_context=memory_ctx)
    user_prompt = render(
        INSIGHTS_USER,
        total_leads=str(total_leads),
        leads_delta=f"{'+' if leads_delta >= 0 else ''}{leads_delta}",
        hot_leads=str(hot_leads),
        appointments_set=str(appts),
        conversion_rate="N/A",
        avg_score=str(avg_score),
        top_objections=top_objections,
        sms_response_rate="N/A",
        qa_avg_score=str(qa_avg),
        best_counties="N/A",
        top_scripts="N/A",
    )

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="weekly_insights",
    ))

    save_ai_run_sync(db, result)
    return result


# ── Memory Learning Loop ─────────────────────────────────────────────────


def run_memory_update(db: Session, scope: str = "global") -> dict:
    """Analyze recent analytics and write lessons to ai_memory.

    This is a DETERMINISTIC summarization job: it gathers analytics,
    asks Claude to find patterns, and stores the result. No self-modification.
    """
    now = datetime.now(tz=timezone.utc)
    week_ago = now - timedelta(days=7)

    # Gather data: objection frequencies
    objections = db.execute(
        select(ObjectionTag.tag, func.count(ObjectionTag.id).label("cnt"))
        .where(ObjectionTag.created_at >= week_ago)
        .group_by(ObjectionTag.tag)
        .order_by(func.count(ObjectionTag.id).desc())
        .limit(20)
    ).all()

    # NBA outcome data
    nba_applied = db.execute(
        select(NBADecision.recommended_action, func.count(NBADecision.id))
        .where(NBADecision.created_at >= week_ago, NBADecision.applied == True)
        .group_by(NBADecision.recommended_action)
    ).all()

    # QA scores
    qa_avg = db.execute(
        select(func.avg(QAReview.compliance_score)).where(QAReview.created_at >= week_ago)
    ).scalar()

    data_summary = json.dumps({
        "objection_frequencies": {t: c for t, c in objections},
        "nba_outcomes": {str(a): c for a, c in nba_applied},
        "qa_average": round(qa_avg or 0, 1),
        "period": f"{week_ago.date()} to {now.date()}",
    }, indent=2)

    system_prompt = MEMORY_SYSTEM
    user_prompt = render(
        MEMORY_USER,
        time_period=f"{week_ago.date()} to {now.date()}",
        scope=scope,
        data=data_summary,
    )

    ai = get_claude_client()
    result = _run_async(ai.chat(
        system_prompt, user_prompt,
        task_type="memory_update",
    ))

    save_ai_run_sync(db, result)

    # Write lessons to memory
    lessons = result.get("lessons", [])
    if lessons:
        upsert_memory_sync(
            db, scope, "weekly_lessons",
            "\n".join(f"- {l}" for l in lessons),
            meta_json={"source": "weekly_analysis", "date": now.isoformat()},
        )

    patterns = result.get("patterns", [])
    if patterns:
        upsert_memory_sync(
            db, scope, "objection_patterns",
            json.dumps(patterns),
            meta_json={"source": "weekly_analysis", "date": now.isoformat()},
        )

    return result
