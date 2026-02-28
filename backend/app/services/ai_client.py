"""Provider-agnostic AI client for structured JSON outputs.

Supports OpenAI-compatible APIs. Swap provider by changing OPENAI_API_KEY
and optionally OPENAI_BASE_URL.
"""

import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_TIMEOUT = 30.0


class AIClient:
    """Thin wrapper around an OpenAI-compatible chat completions API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.model = settings.ai_model
        self.temperature = settings.ai_temperature
        self.max_tokens = settings.ai_max_tokens
        self.base_url = settings.ai_base_url

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request and return parsed JSON.

        If the AI provider is not configured, returns a deterministic fallback.
        """
        if not self.enabled:
            return self._fallback(system_prompt, user_prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if response_format:
            body["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_text": content}

        except Exception as e:
            logger.warning("AI request failed: %s — using fallback", e)
            return self._fallback(system_prompt, user_prompt)

    def _fallback(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Deterministic fallback when AI is not available."""
        # Detect prompt type from system prompt keywords and return safe defaults
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
            return {"tags": [], "confidence": 0.0, "evidence_spans": []}
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
        # Generic fallback
        return {"raw_text": "AI provider not configured", "fallback": True}


# Module-level singleton
_client: AIClient | None = None


def get_ai_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
