"""Celery tasks for the AI Operator: scheduled processing, NBA batch, weekly runs."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.tasks import (
    run_memory_update,
    run_nba,
    run_objection_extraction,
    run_qa_review,
    run_weekly_insights,
)
from app.ai.storage import save_ai_run_sync
from app.core.config import get_settings
from app.models.schema import (
    ContactChannel,
    ConversationTranscript,
    Lead,
    LeadStatus,
    NBAAction,
    NBADecision,
    ObjectionTag,
    QAReview,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

settings = get_settings()
sync_engine = create_engine(settings.database_url_sync, echo=False)


@celery_app.task(name="app.workers.ai_operator_tasks.task_process_new_conversations")
def task_process_new_conversations():
    """Process conversations that haven't been QA'd or tagged yet.

    Runs every 5 minutes. Picks up conversations created in the last hour
    that don't have a QA review yet.
    """
    with Session(sync_engine) as db:
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=1)

        # Find conversations without QA reviews
        reviewed_ids = select(QAReview.conversation_id).where(QAReview.conversation_id.isnot(None))
        unreviewed = db.execute(
            select(ConversationTranscript.id)
            .where(
                ConversationTranscript.created_at >= cutoff,
                ConversationTranscript.id.notin_(reviewed_ids),
            )
            .limit(10)
        ).scalars().all()

        processed = 0
        for convo_id in unreviewed:
            try:
                # Run QA review
                result = run_qa_review(db, convo_id)
                if result:
                    review = QAReview(
                        lead_id=result.get("lead_id", 0),
                        conversation_id=convo_id,
                        compliance_score=result.get("compliance_score", 70),
                        flags=result.get("flags", []),
                        checklist_pass=result.get("checklist_pass", True),
                        rationale=result.get("rationale", ""),
                        reviewed_by="ai_operator",
                        ai_output=result,
                        ai_model="claude",
                    )
                    # Get lead_id from conversation
                    convo = db.get(ConversationTranscript, convo_id)
                    if convo:
                        review.lead_id = convo.lead_id
                    db.add(review)

                # Extract objections
                obj_result = run_objection_extraction(db, convo_id)
                for tag_data in obj_result.get("tags", []):
                    if isinstance(tag_data, dict):
                        convo = db.get(ConversationTranscript, convo_id)
                        tag = ObjectionTag(
                            conversation_id=convo_id,
                            lead_id=convo.lead_id if convo else 0,
                            tag=tag_data.get("tag", "unknown"),
                            confidence=tag_data.get("confidence", 0.0),
                            evidence_span=tag_data.get("evidence_span", ""),
                            ai_output=tag_data,
                        )
                        db.add(tag)

                processed += 1
            except Exception as e:
                logger.error("Failed to process conversation %d: %s", convo_id, e)

        db.commit()
        logger.info("Processed %d new conversations", processed)


@celery_app.task(name="app.workers.ai_operator_tasks.task_nightly_nba_batch")
def task_nightly_nba_batch():
    """Recompute NBA for all leads in active outreach statuses.

    Runs nightly at 2am ET. Only processes leads that are in
    contacting/contacted/nurturing status and don't have a fresh NBA decision.
    """
    with Session(sync_engine) as db:
        active_statuses = [
            LeadStatus.contacting, LeadStatus.contacted,
            LeadStatus.nurturing, LeadStatus.scored,
            LeadStatus.hot, LeadStatus.warm,
        ]

        # Get leads needing NBA update (no decision in last 24h)
        cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        recent_nba_leads = (
            select(NBADecision.lead_id)
            .where(NBADecision.created_at >= cutoff)
            .distinct()
        )

        leads = db.execute(
            select(Lead.id)
            .where(
                Lead.status.in_(active_statuses),
                Lead.id.notin_(recent_nba_leads),
            )
            .limit(100)  # Process max 100 per run to control API costs
        ).scalars().all()

        processed = 0
        for lead_id in leads:
            try:
                result = run_nba(db, lead_id)
                if result and result.get("next_action"):
                    # Map action string to enum
                    action_map = {
                        "call": NBAAction.call, "sms": NBAAction.sms,
                        "email": NBAAction.email, "wait": NBAAction.wait,
                        "rep_handoff": NBAAction.rep_handoff,
                        "nurture": NBAAction.nurture, "close": NBAAction.close,
                    }
                    action = action_map.get(result["next_action"], NBAAction.wait)

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
                        ai_model="claude",
                        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
                    )
                    db.add(decision)
                    processed += 1
            except Exception as e:
                logger.error("NBA failed for lead %d: %s", lead_id, e)

        db.commit()
        logger.info("Nightly NBA batch: processed %d leads", processed)


@celery_app.task(name="app.workers.ai_operator_tasks.task_weekly_operator_run")
def task_weekly_operator_run():
    """Weekly AI Operator run: insights + memory update.

    Runs Monday 7am ET. Generates weekly insights narrative and
    updates organizational memory with lessons learned.
    """
    with Session(sync_engine) as db:
        try:
            # 1. Generate weekly insights
            insights = run_weekly_insights(db)
            logger.info("Weekly insights generated: %s", insights.get("narrative", "")[:100])

            # 2. Update organizational memory
            memory_result = run_memory_update(db, scope="global")
            lessons = memory_result.get("lessons", [])
            logger.info("Memory update: %d lessons learned", len(lessons))

            db.commit()
        except Exception as e:
            logger.error("Weekly operator run failed: %s", e)
            db.rollback()


@celery_app.task(name="app.workers.ai_operator_tasks.task_recompute_nba")
def task_recompute_nba(lead_id: int):
    """On-demand NBA recomputation (called from API)."""
    with Session(sync_engine) as db:
        result = run_nba(db, lead_id)
        if result and result.get("next_action"):
            action_map = {
                "call": NBAAction.call, "sms": NBAAction.sms,
                "email": NBAAction.email, "wait": NBAAction.wait,
                "rep_handoff": NBAAction.rep_handoff,
                "nurture": NBAAction.nurture, "close": NBAAction.close,
            }
            action = action_map.get(result["next_action"], NBAAction.wait)

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
                ai_model="claude",
                expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
            )
            db.add(decision)
            db.commit()
            return {"status": "computed", "action": result["next_action"]}
        db.commit()
        return {"status": "no_result"}


@celery_app.task(name="app.workers.ai_operator_tasks.task_generate_rep_brief")
def task_generate_rep_brief(lead_id: int):
    """On-demand rep brief generation (called from API)."""
    from app.ai.tasks import run_rep_brief
    with Session(sync_engine) as db:
        result = run_rep_brief(db, lead_id)
        db.commit()
        return result
