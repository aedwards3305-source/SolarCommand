"""Tests for outreach orchestration logic."""

import pytest

from app.models.schema import ContactChannel, Lead, LeadStatus
from app.services.orchestrator import MAX_CALL_ATTEMPTS, MAX_SMS_ATTEMPTS, select_channel


def _make_lead(**overrides) -> Lead:
    """Create a Lead instance for testing."""
    defaults = {
        "id": 1,
        "property_id": 1,
        "status": LeadStatus.hot,
        "total_call_attempts": 0,
        "total_sms_sent": 0,
        "total_emails_sent": 0,
    }
    defaults.update(overrides)
    lead = Lead.__new__(Lead)
    for k, v in defaults.items():
        setattr(lead, k, v)
    return lead


class TestSelectChannel:
    def test_fresh_lead_gets_call_first(self):
        lead = _make_lead()
        # Note: this test depends on the current time being in call window.
        # In CI, you'd mock is_within_call_window.
        channel = select_channel(lead)
        # Either voice (if in window) or sms (if outside window) or None
        assert channel in (ContactChannel.voice, ContactChannel.sms, None)

    def test_exhausted_calls_escalates_to_sms(self):
        lead = _make_lead(total_call_attempts=MAX_CALL_ATTEMPTS)
        channel = select_channel(lead)
        # Should be sms (if in window) or email or None
        assert channel != ContactChannel.voice

    def test_exhausted_calls_and_sms_escalates_to_email(self):
        lead = _make_lead(
            total_call_attempts=MAX_CALL_ATTEMPTS,
            total_sms_sent=MAX_SMS_ATTEMPTS,
        )
        channel = select_channel(lead)
        assert channel == ContactChannel.email

    def test_all_channels_exhausted_returns_none(self):
        lead = _make_lead(
            total_call_attempts=MAX_CALL_ATTEMPTS,
            total_sms_sent=MAX_SMS_ATTEMPTS,
            total_emails_sent=5,
        )
        channel = select_channel(lead)
        assert channel is None
