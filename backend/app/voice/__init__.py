"""Voice integration — provider-agnostic outbound calling."""

from app.voice.base import VoiceProvider
from app.voice.factory import get_voice_provider

__all__ = ["VoiceProvider", "get_voice_provider"]
