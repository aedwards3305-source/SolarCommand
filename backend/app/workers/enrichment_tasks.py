"""Celery tasks for contact enrichment and validation."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.enrichment_tasks.task_enrich_contact",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def task_enrich_contact(self, lead_id: int):
    """Enrich a lead via PDL — only Hot/Warm leads above confidence threshold."""
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from app.core.database import async_engine
    from app.enrichment.pipeline import enrich_lead
    from app.models.schema import Lead

    async def _run():
        async with AS(async_engine) as db:
            lead = await db.get(Lead, lead_id)
            if not lead:
                logger.error("Enrichment task: lead %d not found", lead_id)
                return

            result = await enrich_lead(db, lead)
            await db.commit()

            if result:
                logger.info("Lead %d enriched (confidence=%.2f)", lead_id, result.confidence)
            else:
                logger.info("Lead %d enrichment skipped or failed", lead_id)

    asyncio.run(_run())


@celery_app.task(
    name="app.workers.enrichment_tasks.task_validate_contact",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def task_validate_contact(self, lead_id: int):
    """Validate a lead's phone/email via Melissa."""
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from app.core.database import async_engine
    from app.enrichment.pipeline import validate_contact
    from app.models.schema import Lead

    async def _run():
        async with AS(async_engine) as db:
            lead = await db.get(Lead, lead_id)
            if not lead:
                logger.error("Validation task: lead %d not found", lead_id)
                return

            result = await validate_contact(db, lead)
            await db.commit()

            if result:
                logger.info(
                    "Lead %d validated (phone_valid=%s, confidence=%.2f)",
                    lead_id, result.phone_valid, result.confidence,
                )

    asyncio.run(_run())


@celery_app.task(
    name="app.workers.enrichment_tasks.task_enrich_batch",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
)
def task_enrich_batch(self):
    """Batch enrichment: enrich all Hot/Warm leads that haven't been enriched yet."""
    import asyncio
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession as AS
    from app.core.database import async_engine
    from app.models.schema import ContactEnrichment, Lead, LeadStatus

    async def _run():
        async with AS(async_engine) as db:
            # Find hot/warm leads without enrichment
            enriched_subq = (
                select(ContactEnrichment.lead_id)
                .distinct()
                .subquery()
            )
            result = await db.execute(
                select(Lead.id)
                .where(Lead.status.in_([LeadStatus.hot, LeadStatus.warm]))
                .where(Lead.id.notin_(select(enriched_subq.c.lead_id)))
                .limit(50)  # batch cap
            )
            lead_ids = [row[0] for row in result.all()]

        logger.info("Batch enrichment: %d leads to process", len(lead_ids))
        for lid in lead_ids:
            task_enrich_contact.delay(lid)
            task_validate_contact.delay(lid)

    asyncio.run(_run())
