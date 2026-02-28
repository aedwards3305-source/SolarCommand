"""Celery tasks for voice call placement and follow-up."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.voice_tasks.task_place_voice_call",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
)
def task_place_voice_call(self, lead_id: int, script_version_id: int | None = None):
    """Place an outbound voice call for a lead.

    Safety gates:
    - Lead must not be DNC / opted-out / terminal
    - Must be within allowed call hours
    - Consent check must pass

    Dispatches AI follow-up tasks on call completion.
    """
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from app.core.database import async_engine
    from app.models.schema import (
        AuditLog,
        ContactChannel,
        ConversationTranscript,
        Lead,
        LeadStatus,
        OutreachAttempt,
        ScriptVersion,
    )
    from app.services.compliance import check_can_message, is_within_quiet_hours
    from app.voice.factory import get_voice_provider

    async def _run():
        async with AS(async_engine) as db:
            lead = await db.get(Lead, lead_id)
            if not lead:
                logger.error("Voice task: lead %d not found", lead_id)
                return

            # ── Safety gates ───────────────────────────────────────────
            terminal = {
                LeadStatus.closed_won, LeadStatus.closed_lost,
                LeadStatus.dnc, LeadStatus.archived, LeadStatus.disqualified,
            }
            if lead.status in terminal:
                logger.info("Lead %d in terminal status %s — skipping call", lead_id, lead.status.value)
                return

            can_msg, reason = await check_can_message(db, lead)
            if not can_msg:
                logger.info("Lead %d cannot be contacted: %s", lead_id, reason)
                return

            if not lead.phone:
                logger.info("Lead %d has no phone number", lead_id)
                return

            # ── Get script text ────────────────────────────────────────
            script_text = None
            if script_version_id:
                sv = await db.get(ScriptVersion, script_version_id)
                if sv:
                    script_text = sv.content

            # ── Place call ─────────────────────────────────────────────
            provider = get_voice_provider()
            logger.info("Placing %s call to lead %d (%s)", provider.name, lead_id, lead.phone)

            result = await provider.place_call(
                to_number=lead.phone,
                from_number=None,  # uses provider default
                script_text=script_text,
                metadata={
                    "lead_id": lead_id,
                    "script_version_id": script_version_id,
                },
            )

            # ── Record outreach attempt ────────────────────────────────
            attempt = OutreachAttempt(
                lead_id=lead_id,
                channel=ContactChannel.voice,
                external_call_id=result.call_sid,
                script_version_id=script_version_id,
            )
            db.add(attempt)

            # Create transcript record (will be updated when call completes)
            convo = ConversationTranscript(
                lead_id=lead_id,
                channel=ContactChannel.voice,
                raw_transcript="",
                provider=provider.name,
                call_sid=result.call_sid,
                call_status=result.status,
            )
            db.add(convo)

            # Update lead tracking
            from datetime import datetime, timezone
            lead.last_contacted_at = datetime.now(timezone.utc)
            lead.total_call_attempts += 1
            if lead.status == LeadStatus.scored:
                lead.status = LeadStatus.contacting

            # Audit
            db.add(AuditLog(
                actor="ai_agent",
                action="voice.call_placed",
                entity_type="lead",
                entity_id=lead_id,
                new_value=f"{provider.name}:{result.call_sid}",
                metadata_json={
                    "provider": provider.name,
                    "call_sid": result.call_sid,
                    "status": result.status,
                },
            ))

            await db.commit()
            logger.info(
                "Call placed for lead %d — call_sid=%s, status=%s",
                lead_id, result.call_sid, result.status,
            )

    asyncio.run(_run())


@celery_app.task(
    name="app.workers.voice_tasks.task_process_call_completion",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def task_process_call_completion(self, call_sid: str, provider_name: str):
    """Process a completed call — fetch recording, transcript, trigger AI tasks."""
    import asyncio
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from app.core.database import async_engine
    from app.models.schema import ConversationTranscript
    from app.voice.factory import get_voice_provider
    from app.workers.ai_tasks import (
        task_extract_objections,
        task_generate_transcript_summary,
        task_run_qa_review,
    )

    async def _run():
        provider = get_voice_provider(override=provider_name)

        # Fetch final status
        status = await provider.get_call_status(call_sid)
        recording_url = await provider.get_recording_url(call_sid)

        async with AS(async_engine) as db:
            result = await db.execute(
                select(ConversationTranscript)
                .where(ConversationTranscript.call_sid == call_sid)
                .limit(1)
            )
            convo = result.scalar_one_or_none()

            if not convo:
                logger.warning("No conversation record for call_sid=%s", call_sid)
                return

            # Update record
            convo.call_status = status.status
            convo.duration_seconds = status.duration_seconds
            if recording_url:
                convo.recording_url = recording_url
            if status.transcript:
                convo.raw_transcript = status.transcript

            await db.commit()

            # Dispatch AI tasks if we have a transcript
            if convo.raw_transcript:
                task_generate_transcript_summary.delay(convo.id)
                task_run_qa_review.delay(convo.id)
                task_extract_objections.delay(convo.id)

            logger.info(
                "Call %s completed — duration=%ss, has_recording=%s, has_transcript=%s",
                call_sid, status.duration_seconds,
                bool(recording_url), bool(convo.raw_transcript),
            )

    asyncio.run(_run())
