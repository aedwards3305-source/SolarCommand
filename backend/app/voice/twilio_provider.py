"""Twilio voice provider — outbound calls via Twilio Programmable Voice."""

import asyncio
import logging
from xml.sax.saxutils import escape as xml_escape

from app.core.config import get_settings
from app.voice.base import CallResult, CallStatus, VoiceProvider

logger = logging.getLogger(__name__)


class TwilioVoiceProvider(VoiceProvider):
    """Twilio implementation of VoiceProvider."""

    @property
    def name(self) -> str:
        return "twilio"

    def __init__(self) -> None:
        settings = get_settings()
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_phone_number
        self._client = None

    def _get_client(self):
        """Lazy-init Twilio client."""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                logger.error("twilio package not installed — pip install twilio")
                raise
        return self._client

    @property
    def enabled(self) -> bool:
        return bool(self.account_sid and self.auth_token)

    async def place_call(
        self,
        to_number: str,
        from_number: str | None = None,
        script_text: str | None = None,
        webhook_url: str | None = None,
        metadata: dict | None = None,
    ) -> CallResult:
        if not self.enabled:
            logger.warning("Twilio not configured — returning stub call")
            return CallResult(
                call_sid="stub-twilio-not-configured",
                status="failed",
                provider=self.name,
                to_number=to_number,
                from_number=from_number or self.from_number,
            )

        client = self._get_client()

        # Build TwiML or use webhook_url for call instructions
        call_params = {
            "to": to_number,
            "from_": from_number or self.from_number,
        }

        if webhook_url:
            call_params["url"] = webhook_url
        else:
            # Default: simple TwiML that says the script and records
            twiml = '<Response><Say voice="Polly.Matthew">'
            if script_text:
                # Full XML entity escaping (& < > " ')
                safe_text = xml_escape(script_text, {'"': "&quot;", "'": "&apos;"})
                twiml += safe_text
            else:
                twiml += "Hello, this is a call from SolarCommand."
            twiml += "</Say></Response>"
            call_params["twiml"] = twiml

        call_params["record"] = True
        call_params["recording_status_callback"] = (
            (metadata or {}).get("recording_callback_url", "")
        )

        if metadata and metadata.get("status_callback_url"):
            call_params["status_callback"] = metadata["status_callback_url"]
            call_params["status_callback_event"] = [
                "initiated", "ringing", "answered", "completed",
            ]

        # Run blocking Twilio SDK call in a thread to avoid blocking the event loop
        call = await asyncio.to_thread(client.calls.create, **call_params)

        return CallResult(
            call_sid=call.sid,
            status=call.status,
            provider=self.name,
            to_number=to_number,
            from_number=from_number or self.from_number,
        )

    async def get_call_status(self, call_sid: str) -> CallStatus:
        if not self.enabled:
            return CallStatus(call_sid=call_sid, status="unknown")

        client = self._get_client()
        call = await asyncio.to_thread(client.calls(call_sid).fetch)

        return CallStatus(
            call_sid=call.sid,
            status=call.status,
            duration_seconds=int(call.duration) if call.duration else None,
        )

    async def get_recording_url(self, call_sid: str) -> str | None:
        if not self.enabled:
            return None

        client = self._get_client()
        recordings = await asyncio.to_thread(
            client.recordings.list, call_sid=call_sid, limit=1
        )
        if recordings:
            return f"https://api.twilio.com{recordings[0].uri.replace('.json', '.mp3')}"
        return None

    def parse_webhook(self, payload: dict) -> CallStatus:
        return CallStatus(
            call_sid=payload.get("CallSid", ""),
            status=payload.get("CallStatus", "unknown"),
            duration_seconds=(
                int(payload["CallDuration"]) if payload.get("CallDuration") else None
            ),
            recording_url=payload.get("RecordingUrl"),
        )
