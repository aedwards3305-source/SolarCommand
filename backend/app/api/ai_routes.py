"""AI Operator API routes — rep brief, objections, admin runs, script suggest, insights.

All routes under /ai/ prefix. Admin routes require admin role.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.schema import (
    AIRun,
    ContactEnrichment,
    ContactValidation,
    ConversationTranscript,
    Lead,
    ObjectionTag,
    ScriptVersion,
)
from app.workers.ai_operator_tasks import task_generate_rep_brief, task_recompute_nba

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


# ── Response models ─────────────────────────────────────────────────────


class RepBriefResponse(BaseModel):
    summary: str
    talk_track: list[str]
    objection_handlers: list[str]
    recommended_approach: str
    risk_factors: list[str] | None = None


class ObjectionOut(BaseModel):
    id: int
    tag: str
    confidence: float
    evidence_span: str | None
    created_at: str


class AIRunOut(BaseModel):
    id: int
    task_type: str
    lead_id: int | None
    conversation_id: int | None
    model: str
    temperature: float | None
    prompt_version: str | None
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    latency_ms: int | None
    status: str
    error: str | None
    created_at: str


class AIRunsListResponse(BaseModel):
    runs: list[AIRunOut]
    total: int


class ScriptSuggestResponse(BaseModel):
    edits: list[dict]
    hypotheses: list[str]
    expected_lift: float


class AIStatsResponse(BaseModel):
    total_runs_today: int
    errors_today: int
    avg_latency_ms: float
    total_cost_today: float
    runs_by_task: dict[str, int]


# ── Lead-level routes ───────────────────────────────────────────────────


@router.get("/leads/{lead_id}/rep-brief", response_model=RepBriefResponse)
async def get_rep_brief(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Generate an AI rep brief for a lead (on-demand)."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Dispatch to Celery and return immediately with a computing status,
    # or run synchronously for small payloads. For now, run via Celery.
    result = task_generate_rep_brief.delay(lead_id)

    # Return a placeholder — the frontend polls or the brief is cached.
    return RepBriefResponse(
        summary="Generating AI brief... Refresh in a few seconds.",
        talk_track=[],
        objection_handlers=[],
        recommended_approach="Brief is being computed by AI Operator.",
    )


@router.get("/leads/{lead_id}/rep-brief/result", response_model=RepBriefResponse)
async def get_rep_brief_result(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get the most recent AI rep brief result from ai_run table."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(AIRun)
        .where(AIRun.lead_id == lead_id, AIRun.task_type == "rep_brief", AIRun.status == "success")
        .order_by(AIRun.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()

    if not run or not run.output_json:
        raise HTTPException(status_code=404, detail="No brief available yet")

    data = run.output_json
    return RepBriefResponse(
        summary=data.get("summary", ""),
        talk_track=data.get("talk_track", []),
        objection_handlers=data.get("objection_handlers", []),
        recommended_approach=data.get("recommended_approach", ""),
        risk_factors=data.get("risk_factors"),
    )


@router.get("/leads/{lead_id}/objections", response_model=list[ObjectionOut])
async def get_lead_objections(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get all objection tags for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(ObjectionTag)
        .where(ObjectionTag.lead_id == lead_id)
        .order_by(ObjectionTag.created_at.desc())
    )
    tags = result.scalars().all()

    return [
        ObjectionOut(
            id=t.id,
            tag=t.tag,
            confidence=t.confidence,
            evidence_span=t.evidence_span,
            created_at=t.created_at.isoformat() if t.created_at else "",
        )
        for t in tags
    ]


# ── Admin routes ────────────────────────────────────────────────────────


@router.get(
    "/admin/runs",
    response_model=AIRunsListResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_ai_runs(
    task_type: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List AI runs with optional filters (admin only)."""
    query = select(AIRun).order_by(AIRun.created_at.desc())

    if task_type:
        query = query.where(AIRun.task_type == task_type)
    if status:
        query = query.where(AIRun.status == status)

    # Count
    count_query = select(func.count(AIRun.id))
    if task_type:
        count_query = count_query.where(AIRun.task_type == task_type)
    if status:
        count_query = count_query.where(AIRun.status == status)

    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset(offset).limit(limit))
    runs = result.scalars().all()

    return AIRunsListResponse(
        runs=[
            AIRunOut(
                id=r.id,
                task_type=r.task_type,
                lead_id=r.lead_id,
                conversation_id=r.conversation_id,
                model=r.model,
                temperature=r.temperature,
                prompt_version=r.prompt_version,
                tokens_in=r.tokens_in or 0,
                tokens_out=r.tokens_out or 0,
                cost_usd=r.cost_usd,
                latency_ms=r.latency_ms,
                status=r.status or "unknown",
                error=r.error,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in runs
        ],
        total=total,
    )


@router.get(
    "/admin/runs/{run_id}",
    dependencies=[Depends(require_role("admin"))],
)
async def get_ai_run_detail(run_id: int, db: AsyncSession = Depends(get_db)):
    """Get full AI run detail including input/output JSON (admin only)."""
    run = await db.get(AIRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="AI run not found")

    return {
        "id": run.id,
        "task_type": run.task_type,
        "lead_id": run.lead_id,
        "conversation_id": run.conversation_id,
        "model": run.model,
        "temperature": run.temperature,
        "prompt_version": run.prompt_version,
        "input_json": run.input_json,
        "output_json": run.output_json,
        "tokens_in": run.tokens_in,
        "tokens_out": run.tokens_out,
        "cost_usd": run.cost_usd,
        "latency_ms": run.latency_ms,
        "status": run.status,
        "error": run.error,
        "created_at": run.created_at.isoformat() if run.created_at else "",
    }


@router.post(
    "/admin/scripts/{script_id}/suggest",
    response_model=ScriptSuggestResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def suggest_script_edit(script_id: int, db: AsyncSession = Depends(get_db)):
    """Generate AI script improvement suggestions (admin only)."""
    script = await db.get(ScriptVersion, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # Run synchronously via the task router
    from app.ai.tasks import run_script_suggest

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SyncSession
    from app.core.config import get_settings

    settings = get_settings()
    sync_engine = create_engine(settings.database_url_sync, echo=False)

    with SyncSession(sync_engine) as sync_db:
        result = run_script_suggest(
            sync_db,
            channel=script.channel.value if hasattr(script.channel, "value") else str(script.channel),
            script_version_id=script_id,
        )
        sync_db.commit()

    return ScriptSuggestResponse(
        edits=result.get("edits", []),
        hypotheses=result.get("hypotheses", []),
        expected_lift=result.get("expected_lift", 0.0),
    )


@router.get(
    "/admin/stats",
    response_model=AIStatsResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def get_ai_stats(db: AsyncSession = Depends(get_db)):
    """Get AI Operator stats for today (admin dashboard widget)."""
    today_start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total = (await db.execute(
        select(func.count(AIRun.id)).where(AIRun.created_at >= today_start)
    )).scalar() or 0

    errors = (await db.execute(
        select(func.count(AIRun.id)).where(
            AIRun.created_at >= today_start, AIRun.status == "error"
        )
    )).scalar() or 0

    avg_latency = (await db.execute(
        select(func.avg(AIRun.latency_ms)).where(AIRun.created_at >= today_start)
    )).scalar()

    total_cost = (await db.execute(
        select(func.sum(AIRun.cost_usd)).where(AIRun.created_at >= today_start)
    )).scalar()

    task_counts = await db.execute(
        select(AIRun.task_type, func.count(AIRun.id))
        .where(AIRun.created_at >= today_start)
        .group_by(AIRun.task_type)
    )

    return AIStatsResponse(
        total_runs_today=total,
        errors_today=errors,
        avg_latency_ms=round(avg_latency or 0, 1),
        total_cost_today=round(total_cost or 0, 4),
        runs_by_task={t: c for t, c in task_counts.all()},
    )


# ── Voice routes ───────────────────────────────────────────────────────


class PlaceCallRequest(BaseModel):
    script_version_id: int | None = None


@router.post("/leads/{lead_id}/voice/call")
async def place_voice_call(
    lead_id: int,
    body: PlaceCallRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Place an outbound voice call for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    from app.workers.voice_tasks import task_place_voice_call
    task_place_voice_call.delay(lead_id, body.script_version_id if body else None)

    return {"status": "queued", "lead_id": lead_id}


@router.get("/leads/{lead_id}/voice/recordings")
async def get_lead_recordings(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get voice recordings for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    result = await db.execute(
        select(ConversationTranscript)
        .where(
            ConversationTranscript.lead_id == lead_id,
            ConversationTranscript.recording_url.isnot(None),
        )
        .order_by(ConversationTranscript.created_at.desc())
    )
    convos = result.scalars().all()

    return [
        {
            "id": c.id,
            "call_sid": c.call_sid,
            "provider": c.provider,
            "recording_url": c.recording_url,
            "duration_seconds": c.duration_seconds,
            "call_status": c.call_status,
            "ai_summary": c.ai_summary,
            "ai_sentiment": c.ai_sentiment,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        }
        for c in convos
    ]


# ── Enrichment routes ──────────────────────────────────────────────────


@router.get("/leads/{lead_id}/enrichment")
async def get_lead_enrichment(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Get enrichment + validation data for a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    enrichment_result = await db.execute(
        select(ContactEnrichment)
        .where(ContactEnrichment.lead_id == lead_id)
        .order_by(ContactEnrichment.created_at.desc())
        .limit(1)
    )
    enrichment = enrichment_result.scalar_one_or_none()

    validation_result = await db.execute(
        select(ContactValidation)
        .where(ContactValidation.lead_id == lead_id)
        .order_by(ContactValidation.created_at.desc())
        .limit(1)
    )
    validation = validation_result.scalar_one_or_none()

    return {
        "enrichment": {
            "provider": enrichment.provider,
            "full_name": enrichment.full_name,
            "emails": enrichment.emails,
            "phones": enrichment.phones,
            "job_title": enrichment.job_title,
            "linkedin_url": enrichment.linkedin_url,
            "confidence": enrichment.confidence,
            "updated_at": enrichment.updated_at.isoformat() if enrichment.updated_at else "",
        } if enrichment else None,
        "validation": {
            "provider": validation.provider,
            "phone_valid": validation.phone_valid,
            "phone_type": validation.phone_type,
            "phone_carrier": validation.phone_carrier,
            "email_valid": validation.email_valid,
            "email_deliverable": validation.email_deliverable,
            "address_valid": validation.address_valid,
            "confidence": validation.confidence,
            "updated_at": validation.updated_at.isoformat() if validation.updated_at else "",
        } if validation else None,
    }


@router.post("/leads/{lead_id}/enrichment/run")
async def run_enrichment(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger enrichment + validation for a lead (on-demand)."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    from app.workers.enrichment_tasks import task_enrich_contact, task_validate_contact
    task_enrich_contact.delay(lead_id)
    task_validate_contact.delay(lead_id)

    return {"status": "queued", "lead_id": lead_id}
