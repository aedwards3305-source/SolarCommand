"""AI run persistence and memory store — write ai_run records, read/write ai_memory."""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.schema import AIMemory, AIRun

logger = logging.getLogger(__name__)


def save_ai_run_sync(db: Session, ai_result: dict[str, Any]) -> int | None:
    """Extract _ai_run metadata from an AI result and persist it. Returns ai_run.id."""
    meta = ai_result.pop("_ai_run", None)
    if not meta:
        return None

    run = AIRun(
        task_type=meta["task_type"],
        lead_id=meta.get("lead_id"),
        conversation_id=meta.get("conversation_id"),
        model=meta["model"],
        temperature=meta["temperature"],
        prompt_version=meta["prompt_version"],
        input_json={"hash": meta.get("input_hash", "")},
        output_json=ai_result,
        tokens_in=meta.get("tokens_in", 0),
        tokens_out=meta.get("tokens_out", 0),
        cost_usd=meta.get("cost_usd"),
        latency_ms=meta.get("latency_ms"),
        status=meta.get("status", "success"),
        error=meta.get("error"),
    )
    db.add(run)
    db.flush()
    return run.id


async def save_ai_run_async(db: AsyncSession, ai_result: dict[str, Any]) -> int | None:
    """Async version of save_ai_run_sync."""
    meta = ai_result.pop("_ai_run", None)
    if not meta:
        return None

    run = AIRun(
        task_type=meta["task_type"],
        lead_id=meta.get("lead_id"),
        conversation_id=meta.get("conversation_id"),
        model=meta["model"],
        temperature=meta["temperature"],
        prompt_version=meta["prompt_version"],
        input_json={"hash": meta.get("input_hash", "")},
        output_json=ai_result,
        tokens_in=meta.get("tokens_in", 0),
        tokens_out=meta.get("tokens_out", 0),
        cost_usd=meta.get("cost_usd"),
        latency_ms=meta.get("latency_ms"),
        status=meta.get("status", "success"),
        error=meta.get("error"),
    )
    db.add(run)
    await db.flush()
    return run.id


def upsert_memory_sync(db: Session, scope: str, key: str, content: str, meta_json: dict | None = None) -> None:
    """Write or update an ai_memory entry (deterministic, no AI needed)."""
    existing = db.execute(
        select(AIMemory).where(AIMemory.scope == scope, AIMemory.key == key)
    ).scalar_one_or_none()

    if existing:
        existing.content = content
        existing.meta_json = meta_json
        existing.updated_at = datetime.now(tz=timezone.utc)
    else:
        db.add(AIMemory(scope=scope, key=key, content=content, meta_json=meta_json))


def get_memory_sync(db: Session, scope: str, key: str) -> str | None:
    """Read a single memory entry."""
    mem = db.execute(
        select(AIMemory).where(AIMemory.scope == scope, AIMemory.key == key)
    ).scalar_one_or_none()
    return mem.content if mem else None


def get_memories_by_scope_sync(db: Session, scope: str, limit: int = 20) -> list[dict]:
    """Read all memories for a scope (for RAG injection into prompts)."""
    rows = db.execute(
        select(AIMemory)
        .where(AIMemory.scope == scope)
        .order_by(AIMemory.updated_at.desc())
        .limit(limit)
    ).scalars().all()
    return [{"key": r.key, "content": r.content, "meta": r.meta_json} for r in rows]


async def get_memories_by_scope_async(db: AsyncSession, scope: str, limit: int = 20) -> list[dict]:
    """Async version."""
    result = await db.execute(
        select(AIMemory)
        .where(AIMemory.scope == scope)
        .order_by(AIMemory.updated_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [{"key": r.key, "content": r.content, "meta": r.meta_json} for r in rows]
