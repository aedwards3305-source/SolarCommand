"""Vapi.ai voice provider — AI-driven outbound calls."""

import logging

import httpx

from app.core.config import get_settings
from app.voice.agents.rebecca import build_vapi_assistant
from app.voice.base import CallResult, CallStatus, VoiceProvider

logger = logging.getLogger(__name__)

VAPI_BASE = "https://api.vapi.ai"


class VapiVoiceProvider(VoiceProvider):
    """Vapi.ai implementation of VoiceProvider."""

    @property
    def name(self) -> str:
        return "vapi"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.vapi_api_key
        self.phone_number_id = settings.vapi_phone_number_id
        self.model = settings.vapi_model
        self.webhook_api_key = settings.webhook_api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def place_call(
        self,
        to_number: str,
        from_number: str | None = None,
        script_text: str | None = None,
        webhook_url: str | None = None,
        metadata: dict | None = None,
    ) -> CallResult:
        if not self.enabled:
            logger.warning("Vapi not configured — returning stub call")
            return CallResult(
                call_sid="stub-vapi-not-configured",
                status="failed",
                provider=self.name,
                to_number=to_number,
                from_number=from_number or "",
            )

        # Build the Rebecca agent assistant payload
        server_url = webhook_url or ""
        lead_name = metadata.get("lead_name") if metadata else None
        lead_address = metadata.get("lead_address") if metadata else None

        assistant = build_vapi_assistant(
            server_url=server_url,
            model=self.model,
            lead_name=lead_name,
            lead_address=lead_address,
            lead_phone=to_number,
        )

        # Set the webhook secret so Vapi sends it with tool calls
        if self.webhook_api_key:
            assistant["serverUrlSecret"] = self.webhook_api_key

        payload = {
            "phoneNumberId": self.phone_number_id,
            "customer": {"number": to_number},
            "assistant": assistant,
        }

        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VAPI_BASE}/call/phone",
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return CallResult(
            call_sid=data.get("id", ""),
            status=data.get("status", "queued"),
            provider=self.name,
            to_number=to_number,
            from_number=data.get("phoneNumber", {}).get("number", ""),
        )

    async def get_call_status(self, call_sid: str) -> CallStatus:
        if not self.enabled:
            return CallStatus(call_sid=call_sid, status="unknown")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{VAPI_BASE}/call/{call_sid}",
                headers=self._headers(),
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

        return CallStatus(
            call_sid=call_sid,
            status=data.get("status", "unknown"),
            duration_seconds=data.get("duration"),
            recording_url=data.get("recordingUrl"),
            transcript=data.get("transcript"),
        )

    async def get_recording_url(self, call_sid: str) -> str | None:
        status = await self.get_call_status(call_sid)
        return status.recording_url

    def parse_webhook(self, payload: dict) -> CallStatus:
        msg = payload.get("message", {})
        call = msg.get("call", {})
        return CallStatus(
            call_sid=call.get("id", ""),
            status=msg.get("type", "unknown"),
            duration_seconds=call.get("duration"),
            recording_url=call.get("recordingUrl"),
            transcript=call.get("transcript"),
        )
