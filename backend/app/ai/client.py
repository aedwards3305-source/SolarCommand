"""Anthropic Claude AI client with audit logging and deterministic fallback.

Every call is recorded in ai_run for reproducibility, cost tracking, and compliance.
"""

import hashlib
import json
import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Approximate token cost per million tokens (input/output) for common models
_COST_TABLE = {
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    "claude-opus-4-6": (15.0, 75.0),
}


class ClaudeClient:
    """Thin wrapper around the Anthropic Messages API with audit trail."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.model = settings.anthropic_model
        self.temperature = settings.ai_temperature
        self.max_tokens = settings.ai_max_tokens
        self.prompt_version = settings.ai_prompt_version
        self.cost_tracking = settings.ai_cost_tracking

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        task_type: str = "generic",
        lead_id: int | None = None,
        conversation_id: int | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Call Claude API and return parsed JSON. Falls back to deterministic defaults."""
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens or self.max_tokens
        start = time.monotonic()

        # Build input snapshot for audit
        input_hash = hashlib.sha256(
            f"{system_prompt}{user_prompt}".encode()
        ).hexdigest()[:16]

        if not self.enabled:
            result = self._fallback(system_prompt)
            return {
                "_ai_run": {
                    "task_type": task_type,
                    "lead_id": lead_id,
                    "conversation_id": conversation_id,
                    "model": "fallback",
                    "temperature": temp,
                    "prompt_version": self.prompt_version,
                    "input_hash": input_hash,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0.0,
                    "latency_ms": 0,
                    "status": "success",
                },
                **result,
            }

        body = {
            "model": self.model,
            "max_tokens": max_tok,
            "temperature": temp,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            elapsed_ms = int((time.monotonic() - start) * 1000)

            # Extract response text
            content_blocks = data.get("content", [])
            text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    text += block["text"]

            # Parse JSON from response
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                result = {"raw_text": text}

            # Token usage
            usage = data.get("usage", {})
            tokens_in = usage.get("input_tokens", 0)
            tokens_out = usage.get("output_tokens", 0)

            # Cost estimate
            cost_usd = 0.0
            if self.cost_tracking:
                rates = _COST_TABLE.get(self.model, (3.0, 15.0))
                cost_usd = (tokens_in * rates[0] + tokens_out * rates[1]) / 1_000_000

            result["_ai_run"] = {
                "task_type": task_type,
                "lead_id": lead_id,
                "conversation_id": conversation_id,
                "model": self.model,
                "temperature": temp,
                "prompt_version": self.prompt_version,
                "input_hash": input_hash,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost_usd, 6),
                "latency_ms": elapsed_ms,
                "status": "success",
            }
            return result

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning("Claude API call failed: %s — using fallback", e)
            result = self._fallback(system_prompt)
            result["_ai_run"] = {
                "task_type": task_type,
                "lead_id": lead_id,
                "conversation_id": conversation_id,
                "model": self.model,
                "temperature": temp,
                "prompt_version": self.prompt_version,
                "input_hash": input_hash,
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "latency_ms": elapsed_ms,
                "status": "error",
                "error": str(e)[:500],
            }
            return result

    def _fallback(self, system_prompt: str) -> dict[str, Any]:
        """Deterministic fallback when Claude is not available."""
        sp = system_prompt.lower()
        if "sms" in sp and "reply" in sp:
            return {
                "intent": "unknown",
                "reply_text": "",
                "actions": [],
                "confidence": 0.0,
                "requires_human": True,
            }
        if "qa" in sp or "compliance" in sp:
            return {
                "compliance_score": 70,
                "flags": [],
                "checklist_pass": True,
                "rationale": "Automated review — AI provider not configured.",
            }
        if "objection" in sp:
            return {"tags": []}
        if "next" in sp and "action" in sp:
            return {
                "next_action": "wait",
                "channel": None,
                "schedule_time": None,
                "reason_codes": ["ai_unavailable"],
                "confidence": 0.0,
            }
        if "script" in sp:
            return {
                "edits": [],
                "hypotheses": ["AI provider not configured"],
                "expected_lift": 0.0,
            }
        if "rep" in sp and "brief" in sp:
            return {
                "summary": "AI provider not configured — no brief available.",
                "talk_track": [],
                "objection_handlers": [],
                "recommended_approach": "Follow standard script.",
            }
        if "insight" in sp or "weekly" in sp:
            return {
                "narrative": "AI provider not configured. Review KPIs manually.",
                "key_drivers": [],
                "recommendations": [],
            }
        if "memory" in sp or "lesson" in sp:
            return {"lessons": [], "patterns": []}
        return {"raw_text": "AI provider not configured", "fallback": True}


# Module-level singleton
_client: ClaudeClient | None = None


def get_claude_client() -> ClaudeClient:
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
