"""Voice provider factory — returns the configured provider instance."""

from app.core.config import get_settings
from app.voice.base import VoiceProvider
from app.voice.twilio_provider import TwilioVoiceProvider
from app.voice.vapi_provider import VapiVoiceProvider

_PROVIDERS: dict[str, type[VoiceProvider]] = {
    "twilio": TwilioVoiceProvider,
    "vapi": VapiVoiceProvider,
}


def get_voice_provider(override: str | None = None) -> VoiceProvider:
    """Return the configured (or overridden) voice provider.

    Priority: override arg > VOICE_PROVIDER env var > 'twilio' default.
    """
    settings = get_settings()
    name = override or settings.voice_provider

    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"Unknown voice provider '{name}'. "
            f"Available: {', '.join(_PROVIDERS)}"
        )
    return cls()
