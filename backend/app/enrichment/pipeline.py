"""Enrichment pipeline — orchestrates PDL enrichment + Melissa validation."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.enrichment.melissa import MelissaClient
from app.enrichment.pdl import PDLClient
from app.models.schema import (
    ContactEnrichment,
    ContactIntelligence,
    ContactValidation,
    Lead,
    LeadStatus,
)

logger = logging.getLogger(__name__)


async def enrich_lead(db: AsyncSession, lead: Lead) -> ContactEnrichment | None:
    """Run PDL enrichment for a lead. Only enriches Hot/Warm/Scored leads.

    Returns the ContactEnrichment record or None if skipped/failed.
    Uses address-based lookup for leads without name/phone (e.g. SDAT imports).
    """
    from app.models.schema import Property

    settings = get_settings()

    # Gate: only enrich hot/warm/scored/cool/ingested leads
    enrichable = (
        LeadStatus.hot, LeadStatus.warm, LeadStatus.scored,
        LeadStatus.cool, LeadStatus.ingested,
    )
    if lead.status not in enrichable:
        logger.info("Lead %d status %s — skipping enrichment", lead.id, lead.status.value)
        return None

    pdl = PDLClient()
    if not pdl.enabled:
        return None

    # Build the best identifier set
    name_parts = []
    if lead.first_name:
        name_parts.append(lead.first_name)
    if lead.last_name:
        name_parts.append(lead.last_name)
    name = " ".join(name_parts) if name_parts else None

    # Build address for address-based lookups (critical for SDAT leads with no name/phone)
    address = None
    prop = await db.get(Property, lead.property_id)
    if prop:
        addr_parts = [prop.address_line1, prop.city, prop.state, prop.zip_code]
        address = ", ".join(p for p in addr_parts if p)

    result = await pdl.enrich_person(
        name=name,
        phone=lead.phone,
        email=lead.email,
        address=address,
        city=prop.city if prop else None,
        state=prop.state if prop else None,
        zip_code=prop.zip_code if prop else None,
    )

    if not result:
        return None

    # Check confidence threshold
    if result.get("confidence", 0) < settings.enrichment_confidence_min:
        logger.info(
            "Lead %d enrichment below confidence threshold (%.2f < %.2f)",
            lead.id, result["confidence"], settings.enrichment_confidence_min,
        )
        return None

    enrichment = ContactEnrichment(
        lead_id=lead.id,
        provider="pdl",
        full_name=result.get("full_name"),
        emails=result.get("emails"),
        phones=result.get("phones"),
        job_title=result.get("job_title"),
        linkedin_url=result.get("linkedin_url"),
        confidence=result.get("confidence", 0.0),
        raw_response=result.get("raw_response"),
    )
    db.add(enrichment)

    # Backfill lead contact fields from enrichment
    phones = result.get("phones") or []
    emails = result.get("emails") or []
    if phones and not lead.phone:
        first_phone = phones[0]
        lead.phone = first_phone.get("number") if isinstance(first_phone, dict) else first_phone
    if emails and not lead.email:
        first_email = emails[0]
        lead.email = first_email.get("email") if isinstance(first_email, dict) else first_email
    if result.get("full_name") and not lead.first_name:
        parts = result["full_name"].split(" ", 1)
        lead.first_name = parts[0]
        if len(parts) > 1:
            lead.last_name = parts[1]
        # Also backfill property owner name
        if prop and not prop.owner_first_name:
            prop.owner_first_name = lead.first_name
            prop.owner_last_name = lead.last_name
    # Backfill property owner phone/email
    if prop:
        if lead.phone and not prop.owner_phone:
            prop.owner_phone = lead.phone
        if lead.email and not prop.owner_email:
            prop.owner_email = lead.email

    await db.flush()

    logger.info(
        "Lead %d enriched via PDL (confidence=%.2f, phone=%s, email=%s)",
        lead.id, enrichment.confidence,
        "yes" if lead.phone else "no",
        "yes" if lead.email else "no",
    )
    return enrichment


async def validate_contact(db: AsyncSession, lead: Lead) -> ContactValidation | None:
    """Run Melissa validation for a lead's contact info.

    Returns the ContactValidation record or None if skipped/failed.
    """
    melissa = MelissaClient()
    if not melissa.enabled:
        return None

    # Need at least one field to validate
    if not lead.phone and not lead.email:
        return None

    result = await melissa.validate_contact(
        phone=lead.phone,
        email=lead.email,
    )

    if not result:
        return None

    validation = ContactValidation(
        lead_id=lead.id,
        provider="melissa",
        phone_valid=result.get("phone_valid"),
        phone_type=result.get("phone_type"),
        phone_carrier=result.get("phone_carrier"),
        phone_line_status=result.get("phone_line_status"),
        email_valid=result.get("email_valid"),
        email_deliverable=result.get("email_deliverable"),
        email_disposable=result.get("email_disposable"),
        address_valid=result.get("address_valid"),
        address_deliverable=result.get("address_deliverable"),
        confidence=result.get("confidence", 0.0),
        raw_response=result.get("raw_response"),
    )
    db.add(validation)

    # Also update ContactIntelligence if it exists
    from sqlalchemy import select
    ci_result = await db.execute(
        select(ContactIntelligence).where(ContactIntelligence.lead_id == lead.id).limit(1)
    )
    ci = ci_result.scalar_one_or_none()
    if ci:
        if result.get("phone_valid") is not None:
            ci.phone_valid = result["phone_valid"]
        if result.get("phone_type"):
            ci.phone_type = result["phone_type"]
        if result.get("phone_carrier"):
            ci.carrier_name = result["phone_carrier"]
        if result.get("email_valid") is not None:
            ci.email_valid = result["email_valid"]
        if result.get("email_deliverable") is not None:
            ci.email_deliverable = result["email_deliverable"]

    await db.flush()

    logger.info(
        "Lead %d validated via Melissa (confidence=%.2f, phone_valid=%s)",
        lead.id, validation.confidence, validation.phone_valid,
    )
    return validation


async def skip_trace_leads(
    db: AsyncSession,
    lead_ids: list[int],
    max_wait: int = 300,
) -> dict:
    """Run Tracerfy skip-tracing on a batch of leads.

    Submits addresses to Tracerfy, waits for results, then backfills
    lead contact fields (name, phone, email) and creates ContactEnrichment records.

    Returns summary dict: {submitted, found, not_found, errors}.
    """
    from sqlalchemy import select
    from app.enrichment.tracerfy import TracerfyClient
    from app.models.schema import Property

    client = TracerfyClient()
    if not client.enabled:
        logger.warning("Tracerfy not configured -- skipping skip-trace")
        return {"submitted": 0, "found": 0, "not_found": 0, "errors": 0,
                "error": "TRACERFY_API_KEY not set"}

    # Load leads + properties
    result = await db.execute(
        select(Lead).where(Lead.id.in_(lead_ids))
    )
    leads = {lead.id: lead for lead in result.scalars().all()}

    # Build address list for Tracerfy
    lead_address_map: list[tuple[int, dict]] = []  # (lead_id, address_dict)
    for lid in lead_ids:
        lead = leads.get(lid)
        if not lead:
            continue
        prop = await db.get(Property, lead.property_id)
        if not prop:
            continue
        lead_address_map.append((lid, {
            "address": prop.address_line1 or "",
            "city": prop.city or "",
            "state": prop.state or "MD",
            "zip_code": prop.zip_code or "",
        }))

    if not lead_address_map:
        return {"submitted": 0, "found": 0, "not_found": 0, "errors": 0}

    # Submit to Tracerfy and wait
    addresses = [addr for _, addr in lead_address_map]
    records = await client.trace_and_wait(addresses, max_wait=max_wait)

    logger.info("Tracerfy returned %d results for %d submitted", len(records), len(addresses))

    # Match results back to leads by address
    found = 0
    not_found = 0
    errors = 0

    for i, (lid, addr_dict) in enumerate(lead_address_map):
        lead = leads.get(lid)
        if not lead:
            continue

        # Results are returned in the same order as submitted
        if i >= len(records):
            not_found += 1
            continue

        rec = records[i]

        # Check if Tracerfy found a person
        has_contact = rec.first_name or rec.primary_phone or rec.emails
        if not has_contact:
            not_found += 1
            continue

        found += 1

        # Build phone/email lists for ContactEnrichment
        all_phones = []
        if rec.primary_phone:
            all_phones.append({"number": rec.primary_phone, "type": rec.primary_phone_type or "unknown"})
        for m in (rec.mobiles or []):
            all_phones.append({"number": m, "type": "mobile"})
        for ll in (rec.landlines or []):
            all_phones.append({"number": ll, "type": "landline"})

        all_emails = [{"email": e, "type": "unknown"} for e in (rec.emails or [])]

        full_name = None
        if rec.first_name:
            full_name = f"{rec.first_name} {rec.last_name or ''}".strip()

        # Create ContactEnrichment record
        enrichment = ContactEnrichment(
            lead_id=lid,
            provider="tracerfy",
            full_name=full_name,
            emails=all_emails or None,
            phones=all_phones or None,
            confidence=0.8,  # Tracerfy address match
        )
        db.add(enrichment)

        # Backfill lead contact fields
        if rec.first_name and not lead.first_name:
            lead.first_name = rec.first_name.title()
        if rec.last_name and not lead.last_name:
            lead.last_name = rec.last_name.title()
        if rec.primary_phone and not lead.phone:
            lead.phone = rec.primary_phone
        elif rec.mobiles and not lead.phone:
            lead.phone = rec.mobiles[0]
        if rec.emails and not lead.email:
            lead.email = rec.emails[0]

        # Backfill property owner fields
        prop = await db.get(Property, lead.property_id)
        if prop:
            if not prop.owner_first_name and rec.first_name:
                prop.owner_first_name = lead.first_name
                prop.owner_last_name = lead.last_name
            if lead.phone and not prop.owner_phone:
                prop.owner_phone = lead.phone
            if lead.email and not prop.owner_email:
                prop.owner_email = lead.email

    await db.flush()

    logger.info(
        "Skip-trace complete: %d submitted, %d found, %d not found",
        len(lead_address_map), found, not_found,
    )
    return {
        "submitted": len(lead_address_map),
        "found": found,
        "not_found": not_found,
        "errors": errors,
    }


def enrich_lead_sync(db: Session, lead: Lead) -> None:
    """Synchronous wrapper for Celery tasks — runs enrichment + validation."""
    import asyncio
    from app.core.database import async_engine
    from sqlalchemy.ext.asyncio import AsyncSession as AS

    async def _run():
        async with AS(async_engine) as adb:
            lead_obj = await adb.get(Lead, lead.id)
            if lead_obj:
                await enrich_lead(adb, lead_obj)
                await validate_contact(adb, lead_obj)
                await adb.commit()

    asyncio.run(_run())
