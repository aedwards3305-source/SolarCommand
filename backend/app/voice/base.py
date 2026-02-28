"""Abstract base for voice providers — Twilio, Vapi, Retell."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

# E.164 format: + followed by 1-15 digits, first digit non-zero
_E164_RE = re.compile(r"^\+[1-9]\d{1,14}$")


def validate_e164(phone: str) -> bool:
    """Validate that a phone number is in E.164 format."""
    return bool(_E164_RE.match(phone))


@dataclass
class CallResult:
    """Normalized result from placing an outbound call."""
    call_sid: str
    status: str  # queued, ringing, in-progress, completed, failed
    provider: str  # twilio, vapi, retell
    to_number: str
    from_number: str


@dataclass
class CallStatus:
    """Normalized call status update from webhook."""
    call_sid: str
    status: str
    duration_seconds: int | None = None
    recording_url: str | None = None
    transcript: str | None = None


class VoiceProvider(ABC):
    """Provider-agnostic interface for outbound voice calls."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (twilio, vapi, retell)."""

    @abstractmethod
    async def place_call(
        self,
        to_number: str,
        from_number: str,
        script_text: str | None = None,
        webhook_url: str | None = None,
        metadata: dict | None = None,
    ) -> CallResult:
        """Initiate an outbound call.

        Args:
            to_number: E.164 destination phone number.
            from_number: Caller ID (must be a verified number).
            script_text: Optional script/prompt for AI-driven calls.
            webhook_url: Status callback URL.
            metadata: Extra data passed through to the provider.

        Returns:
            CallResult with the provider's call SID and initial status.
        """

    @abstractmethod
    async def get_call_status(self, call_sid: str) -> CallStatus:
        """Retrieve current status of a call by SID."""

    @abstractmethod
    async def get_recording_url(self, call_sid: str) -> str | None:
        """Retrieve recording URL for a completed call."""

    def parse_webhook(self, payload: dict) -> CallStatus:
        """Parse a provider-specific webhook payload into a CallStatus.

        Default implementation — providers override as needed.
        """
        return CallStatus(
            call_sid=payload.get("call_sid", payload.get("CallSid", "")),
            status=payload.get("status", payload.get("CallStatus", "unknown")),
            duration_seconds=payload.get("duration_seconds"),
            recording_url=payload.get("recording_url", payload.get("RecordingUrl")),
            transcript=payload.get("transcript"),
        )
