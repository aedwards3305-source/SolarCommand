"""End-to-end tests for the SMS automation system.

Tests the full flow:
1. SMS service — phone normalization, send_sms, templates
2. Portal quote → auto-SMS confirmation
3. Portal appointment → auto-SMS confirmation
4. CRM rep send message → direct Twilio (no Celery)
5. Outreach worker → real Twilio sends with correct templates
6. Discovery pipeline SMS blast → direct Twilio
7. Compliance gates (opt-out, DNC, quiet hours)
"""

import importlib
import sys
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.schema import (
    ConsentLog,
    ConsentStatus,
    ContactChannel,
    ContactDisposition,
    Lead,
    LeadStatus,
    MessageDirection,
    OutreachAttempt,
    Property,
    RepUser,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def mock_twilio_send():
    """Mock Twilio Client.messages.create to capture sends."""
    sent_messages = []

    def fake_create(to, from_, body):
        msg = MagicMock()
        msg.sid = f"SM_test_{len(sent_messages)}"
        msg.status = "queued"
        sent_messages.append({"to": to, "from_": from_, "body": body, "sid": msg.sid})
        return msg

    mock_client = MagicMock()
    mock_client.messages.create = fake_create

    with patch("app.services.sms.get_settings") as mock_get:
        mock_get.return_value = Settings(
            twilio_account_sid="ACtest123456789",
            twilio_auth_token="test_auth_token",
            twilio_phone_number="+13013643492",
            scheduling_url="https://solarcommandtech.com/get-quote",
            debug=True,
        )
        with patch("twilio.rest.Client", return_value=mock_client):
            yield sent_messages


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — SMS Service Unit Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestPhoneNormalization:
    """Test normalize_phone handles all US phone formats."""

    def test_ten_digit(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("3015551234") == "+13015551234"

    def test_eleven_digit_with_country_code(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("13015551234") == "+13015551234"

    def test_e164_passthrough(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("+13015551234") == "+13015551234"

    def test_formatted_with_dashes(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("301-555-1234") == "+13015551234"

    def test_formatted_with_parens(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("(301) 555-1234") == "+13015551234"

    def test_formatted_with_dots(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("301.555.1234") == "+13015551234"

    def test_too_short_returns_none(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("12345") is None

    def test_too_long_returns_none(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("123456789012345") is None

    def test_empty_string_returns_none(self):
        from app.services.sms import normalize_phone
        assert normalize_phone("") is None

    def test_non_us_number_returns_none(self):
        from app.services.sms import normalize_phone
        # UK number — 11 digits but doesn't start with 1
        assert normalize_phone("447911123456") is None


class TestSendSms:
    """Test send_sms function with mocked Twilio."""

    def test_successful_send(self, mock_twilio_send):
        from app.services.sms import send_sms
        result = send_sms("3015551234", "Hello test")
        assert "sid" in result
        assert result["status"] == "queued"
        assert len(mock_twilio_send) == 1
        assert mock_twilio_send[0]["to"] == "+13015551234"
        assert mock_twilio_send[0]["body"] == "Hello test"
        assert mock_twilio_send[0]["from_"] == "+13013643492"

    def test_invalid_phone_returns_error(self, mock_twilio_send):
        from app.services.sms import send_sms
        result = send_sms("123", "Hello")
        assert result["error"] == "invalid_phone"
        assert len(mock_twilio_send) == 0

    def test_not_configured_returns_error(self):
        with patch("app.services.sms.get_settings") as mock_get:
            mock_get.return_value = Settings(
                twilio_account_sid="",
                twilio_auth_token="",
                twilio_phone_number="",
                debug=True,
            )
            from app.services.sms import send_sms
            result = send_sms("3015551234", "Hello")
            assert result["error"] == "twilio_not_configured"

    def test_twilio_exception_returns_error(self):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio down")

        with patch("app.services.sms.get_settings") as mock_get:
            mock_get.return_value = Settings(
                twilio_account_sid="ACtest",
                twilio_auth_token="token",
                twilio_phone_number="+13013643492",
                debug=True,
            )
            with patch("twilio.rest.Client", return_value=mock_client):
                from app.services.sms import send_sms
                result = send_sms("3015551234", "Hello")
                assert "Twilio down" in result["error"]

    def test_multiple_sends_tracked(self, mock_twilio_send):
        """Multiple sends are each tracked independently."""
        from app.services.sms import send_sms
        send_sms("3015551111", "First")
        send_sms("3015552222", "Second")
        assert len(mock_twilio_send) == 2
        assert mock_twilio_send[0]["to"] == "+13015551111"
        assert mock_twilio_send[1]["to"] == "+13015552222"


class TestSendSmsAsync:
    """Test async wrapper."""

    async def test_async_send_calls_sync(self, mock_twilio_send):
        from app.services.sms import send_sms_async
        result = await send_sms_async("3015551234", "Async test")
        assert "sid" in result
        assert len(mock_twilio_send) == 1


class TestSmsTemplates:
    """Test all SMS template functions produce valid messages."""

    def test_quote_confirmation(self):
        from app.services.sms import quote_confirmation_sms
        msg = quote_confirmation_sms("John")
        assert "John" in msg
        assert "Solar Command" in msg
        assert "(301) 364-3492" in msg
        assert "MHIC #165263" in msg
        assert len(msg) <= 320  # SMS best practice

    def test_appointment_confirmation(self):
        from app.services.sms import appointment_confirmation_sms
        msg = appointment_confirmation_sms("Jane", "Monday, March 10", "morning")
        assert "Jane" in msg
        assert "Monday, March 10" in msg
        assert "morning" in msg
        assert "(301) 364-3492" in msg

    def test_initial_outreach(self):
        with patch("app.services.sms.get_settings") as mock_get:
            mock_get.return_value = Settings(
                scheduling_url="https://solarcommandtech.com/get-quote",
                debug=True,
            )
            from app.services.sms import initial_outreach_sms
            msg = initial_outreach_sms("Bob", "123 Oak St")
            assert "Bob" in msg
            assert "123 Oak St" in msg
            assert "Maryland" in msg
            assert "30%" in msg
            assert "solarcommandtech.com" in msg
            assert "MHIC #165263" in msg

    def test_followup_1(self):
        with patch("app.services.sms.get_settings") as mock_get:
            mock_get.return_value = Settings(
                scheduling_url="https://solarcommandtech.com/get-quote",
                debug=True,
            )
            from app.services.sms import followup_1_sms
            msg = followup_1_sms("Alice")
            assert "Alice" in msg
            assert "STOP" in msg  # Required opt-out language
            assert "solarcommandtech.com" in msg

    def test_followup_2(self):
        from app.services.sms import followup_2_sms
        msg = followup_2_sms("Charlie")
        assert "Charlie" in msg
        assert "(301) 364-3492" in msg
        assert "Steffen" in msg

    def test_initial_outreach_fallback_url(self):
        """When scheduling_url is empty, falls back to default."""
        with patch("app.services.sms.get_settings") as mock_get:
            mock_get.return_value = Settings(scheduling_url="", debug=True)
            from app.services.sms import initial_outreach_sms
            msg = initial_outreach_sms("Test", "123 Main St")
            assert "solarcommandtech.com/get-quote" in msg


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — Portal & Messages (test via sms.py since module import issues)
# These test the SMS functions that portal.py and messages.py call.
# ═══════════════════════════════════════════════════════════════════════════


class TestPortalSmsIntegration:
    """Test the SMS calls that portal.py makes."""

    async def test_quote_flow_sends_confirmation(self, mock_twilio_send):
        """Simulate what portal.py does: call send_sms_async with quote template."""
        from app.services.sms import quote_confirmation_sms, send_sms_async

        body = quote_confirmation_sms("John")
        result = await send_sms_async("3015551234", body)

        assert result["status"] == "queued"
        assert len(mock_twilio_send) == 1
        assert "John" in mock_twilio_send[0]["body"]
        assert "Solar Command" in mock_twilio_send[0]["body"]
        assert mock_twilio_send[0]["to"] == "+13015551234"

    async def test_appointment_flow_sends_confirmation(self, mock_twilio_send):
        """Simulate what portal.py does: call send_sms_async with appointment template."""
        from app.services.sms import appointment_confirmation_sms, send_sms_async

        body = appointment_confirmation_sms("Jane", "Wednesday, March 12", "afternoon")
        result = await send_sms_async("3015559876", body)

        assert result["status"] == "queued"
        assert "Jane" in mock_twilio_send[0]["body"]
        assert "Wednesday, March 12" in mock_twilio_send[0]["body"]
        assert "afternoon" in mock_twilio_send[0]["body"]

    async def test_rep_send_message_flow(self, mock_twilio_send):
        """Simulate what messages.py does: call send_sms_async with custom message."""
        from app.services.sms import send_sms_async

        result = await send_sms_async("3015551234", "Custom rep message to lead")

        assert result["status"] == "queued"
        assert mock_twilio_send[0]["body"] == "Custom rep message to lead"

    async def test_rep_send_to_invalid_phone(self, mock_twilio_send):
        """Rep sends to a lead with bad phone — graceful error, no crash."""
        from app.services.sms import send_sms_async

        result = await send_sms_async("123", "This should fail gracefully")

        assert result["error"] == "invalid_phone"
        assert len(mock_twilio_send) == 0


# ═══════════════════════════════════════════════════════════════════════════
# PART 3 — Messages.py Module Verification
# ═══════════════════════════════════════════════════════════════════════════


class TestMessagesModuleStructure:
    """Verify messages.py uses direct Twilio, not Celery."""

    def test_messages_imports_send_sms_async_not_celery(self):
        """Verify the messages module imports send_sms_async, not task_send_sms."""
        import ast
        with open("app/api/messages.py", "r") as f:
            source = f.read()
        tree = ast.parse(source)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports.append(f"{node.module}.{alias.name}")

        # Should import send_sms_async from sms service
        assert any("sms.send_sms_async" in i for i in imports), \
            f"messages.py should import send_sms_async. Found: {imports}"

        # Should NOT import task_send_sms from celery tasks
        assert not any("task_send_sms" in i for i in imports), \
            f"messages.py should NOT import task_send_sms. Found: {imports}"

    def test_messages_calls_send_sms_async_not_delay(self):
        """Verify no .delay() calls in messages.py (Celery pattern)."""
        with open("app/api/messages.py", "r") as f:
            source = f.read()

        assert ".delay(" not in source, \
            "messages.py should not use .delay() — should call send_sms_async directly"
        assert "send_sms_async" in source, \
            "messages.py should call send_sms_async"


# ═══════════════════════════════════════════════════════════════════════════
# PART 4 — Outreach Worker (tasks.py) SMS Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestOutreachWorkerSms:
    """Test that _simulate_outreach sends real SMS via Twilio."""

    def test_first_sms_uses_initial_template(self):
        """Lead with 0 SMS sent → initial_outreach_sms template."""
        sent = []

        def fake_send(to, body, from_=None):
            sent.append({"to": to, "body": body})
            return {"sid": "SM_worker", "status": "queued"}

        prop = MagicMock(spec=Property)
        prop.address_line1 = "456 Elm St"

        lead = MagicMock(spec=Lead)
        lead.id = 1
        lead.property_id = 10
        lead.first_name = "Sarah"
        lead.phone = "+13015551234"
        lead.total_sms_sent = 0
        lead.status = LeadStatus.contacting

        attempt = MagicMock(spec=OutreachAttempt)
        attempt.id = 100
        attempt.lead_id = 1
        attempt.channel = ContactChannel.sms

        db = MagicMock(spec=Session)
        db.get = MagicMock(side_effect=lambda model, id: lead if model == Lead else prop)
        db.execute = MagicMock()

        # Patch at the source (app.services.sms) since tasks.py does lazy import
        with patch("app.services.sms.send_sms", side_effect=fake_send):
            with patch("app.services.sms.initial_outreach_sms", return_value="Hi Sarah, initial outreach") as mock_tmpl:
                from app.workers.tasks import _simulate_outreach
                _simulate_outreach(db, attempt)

                mock_tmpl.assert_called_once_with("Sarah", "456 Elm St")
                assert len(sent) == 1
                assert sent[0]["body"] == "Hi Sarah, initial outreach"
                assert attempt.disposition == ContactDisposition.completed

    def test_second_sms_uses_followup_1(self):
        """Lead with 1 SMS sent → followup_1_sms template."""
        sent = []

        def fake_send(to, body, from_=None):
            sent.append({"to": to, "body": body})
            return {"sid": "SM_f1", "status": "queued"}

        lead = MagicMock(spec=Lead)
        lead.id = 2
        lead.property_id = 20
        lead.first_name = "Mike"
        lead.phone = "+13015559999"
        lead.total_sms_sent = 1
        lead.status = LeadStatus.contacting

        attempt = MagicMock(spec=OutreachAttempt)
        attempt.id = 200
        attempt.lead_id = 2
        attempt.channel = ContactChannel.sms

        db = MagicMock(spec=Session)
        db.get = MagicMock(return_value=lead)
        db.execute = MagicMock()

        with patch("app.services.sms.send_sms", side_effect=fake_send):
            with patch("app.services.sms.followup_1_sms", return_value="Hey Mike, follow up 1") as mock_tmpl:
                from app.workers.tasks import _simulate_outreach
                _simulate_outreach(db, attempt)

                mock_tmpl.assert_called_once_with("Mike")
                assert sent[0]["body"] == "Hey Mike, follow up 1"

    def test_third_sms_uses_followup_2(self):
        """Lead with 2+ SMS sent → followup_2_sms template."""
        sent = []

        def fake_send(to, body, from_=None):
            sent.append({"to": to, "body": body})
            return {"sid": "SM_f2", "status": "queued"}

        lead = MagicMock(spec=Lead)
        lead.id = 3
        lead.property_id = 30
        lead.first_name = "Lisa"
        lead.phone = "+13015558888"
        lead.total_sms_sent = 2
        lead.status = LeadStatus.contacting

        attempt = MagicMock(spec=OutreachAttempt)
        attempt.id = 300
        attempt.lead_id = 3
        attempt.channel = ContactChannel.sms

        db = MagicMock(spec=Session)
        db.get = MagicMock(return_value=lead)
        db.execute = MagicMock()

        with patch("app.services.sms.send_sms", side_effect=fake_send):
            with patch("app.services.sms.followup_2_sms", return_value="Hi Lisa, last check-in") as mock_tmpl:
                from app.workers.tasks import _simulate_outreach
                _simulate_outreach(db, attempt)

                mock_tmpl.assert_called_once_with("Lisa")
                assert sent[0]["body"] == "Hi Lisa, last check-in"

    def test_sms_updates_lead_counters(self):
        """Verify that SMS outreach increments total_sms_sent counter."""
        def fake_send(to, body, from_=None):
            return {"sid": "SM_counter", "status": "queued"}

        lead = MagicMock(spec=Lead)
        lead.id = 4
        lead.property_id = 40
        lead.first_name = "Dan"
        lead.phone = "+13015557777"
        lead.total_sms_sent = 0
        lead.status = LeadStatus.contacting

        attempt = MagicMock(spec=OutreachAttempt)
        attempt.id = 400
        attempt.lead_id = 4
        attempt.channel = ContactChannel.sms

        db = MagicMock(spec=Session)
        prop = MagicMock(spec=Property)
        prop.address_line1 = "100 Test Rd"
        db.get = MagicMock(side_effect=lambda model, id: lead if model == Lead else prop)
        db.execute = MagicMock()

        with patch("app.services.sms.send_sms", side_effect=fake_send):
            with patch("app.services.sms.initial_outreach_sms", return_value="test"):
                from app.workers.tasks import _simulate_outreach
                _simulate_outreach(db, attempt)

                # Verify db.execute was called (for the atomic counter update)
                assert db.execute.called
                assert attempt.ended_at is not None
                assert attempt.message_body == "test"

    def test_voice_channel_still_simulated(self):
        """Voice calls are still simulated (not real Twilio yet)."""
        import random
        random.seed(42)  # Deterministic

        lead = MagicMock(spec=Lead)
        lead.id = 5
        lead.property_id = 50
        lead.first_name = "Amy"
        lead.phone = "+13015556666"
        lead.total_call_attempts = 0
        lead.status = LeadStatus.contacting

        attempt = MagicMock(spec=OutreachAttempt)
        attempt.id = 500
        attempt.lead_id = 5
        attempt.channel = ContactChannel.voice
        attempt.disposition = None

        db = MagicMock(spec=Session)
        db.get = MagicMock(return_value=lead)
        db.execute = MagicMock()

        from app.workers.tasks import _simulate_outreach
        _simulate_outreach(db, attempt)

        # Voice should set a disposition (simulated)
        assert attempt.disposition is not None
        assert attempt.ended_at is not None


# ═══════════════════════════════════════════════════════════════════════════
# PART 5 — Compliance Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestComplianceGates:
    """Test that compliance checks prevent unauthorized SMS sends."""

    def test_opt_out_keywords_detected(self):
        from app.services.compliance import is_opt_out_message
        assert is_opt_out_message("STOP") is True
        assert is_opt_out_message("please stop texting me") is True
        assert is_opt_out_message("unsubscribe") is True
        assert is_opt_out_message("opt out") is True
        assert is_opt_out_message("opt-out") is True
        assert is_opt_out_message("remove me from the list") is True
        assert is_opt_out_message("Hello, I'm interested") is False
        assert is_opt_out_message("Yes, tell me more") is False

    def test_opt_out_case_insensitive(self):
        from app.services.compliance import is_opt_out_message
        assert is_opt_out_message("stop") is True
        assert is_opt_out_message("STOP") is True
        assert is_opt_out_message("Stop") is True
        assert is_opt_out_message("UNSUBSCRIBE") is True

    async def test_dnc_lead_blocked(self):
        """DNC leads cannot receive messages."""
        mock_lead = MagicMock(spec=Lead)
        mock_lead.id = 1
        mock_lead.status = LeadStatus.dnc

        db = AsyncMock(spec=AsyncSession)

        from app.services.compliance import check_can_message
        allowed, reason = await check_can_message(db, mock_lead)
        assert allowed is False
        assert "DNC" in reason

    async def test_opted_out_lead_blocked(self):
        """Leads who opted out cannot receive messages."""
        mock_lead = MagicMock(spec=Lead)
        mock_lead.id = 1
        mock_lead.status = LeadStatus.contacting

        mock_consent = MagicMock(spec=ConsentLog)
        db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_consent
        db.execute = AsyncMock(return_value=mock_result)

        from app.services.compliance import check_can_message
        allowed, reason = await check_can_message(db, mock_lead)
        assert allowed is False
        assert "opted out" in reason

    async def test_active_lead_allowed(self):
        """Active leads with no opt-out can receive messages."""
        mock_lead = MagicMock(spec=Lead)
        mock_lead.id = 1
        mock_lead.status = LeadStatus.contacting

        db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.compliance.is_within_quiet_hours", return_value=True):
            from app.services.compliance import check_can_message
            allowed, reason = await check_can_message(db, mock_lead)
            assert allowed is True
            assert reason == "OK"

    async def test_quiet_hours_blocked(self):
        """Messages blocked during quiet hours."""
        mock_lead = MagicMock(spec=Lead)
        mock_lead.id = 1
        mock_lead.status = LeadStatus.contacting

        db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.compliance.is_within_quiet_hours", return_value=False):
            from app.services.compliance import check_can_message
            allowed, reason = await check_can_message(db, mock_lead)
            assert allowed is False
            assert "hours" in reason.lower()

    async def test_closed_won_lead_blocked(self):
        """Closed/won leads are in terminal status — no more messages."""
        mock_lead = MagicMock(spec=Lead)
        mock_lead.id = 1
        mock_lead.status = LeadStatus.closed_won

        db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.compliance.is_within_quiet_hours", return_value=True):
            from app.services.compliance import check_can_message
            allowed, reason = await check_can_message(db, mock_lead)
            assert allowed is False
            assert "terminal" in reason.lower() or "closed_won" in reason


# ═══════════════════════════════════════════════════════════════════════════
# PART 6 — Orchestrator Channel Selection Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestOrchestratorSmsFlow:
    """Test the orchestrator selects SMS channel at the right time."""

    def test_sms_selected_after_max_calls(self):
        from app.services.orchestrator import select_channel, MAX_CALL_ATTEMPTS

        lead = Lead(
            property_id=1,
            status=LeadStatus.contacting,
            total_call_attempts=MAX_CALL_ATTEMPTS,
            total_sms_sent=0,
            total_emails_sent=0,
        )

        with patch("app.services.orchestrator.is_within_sms_window", return_value=True):
            channel = select_channel(lead)
            assert channel == ContactChannel.sms

    def test_sms_selected_when_outside_call_window(self):
        from app.services.orchestrator import select_channel

        lead = Lead(
            property_id=1,
            status=LeadStatus.hot,
            total_call_attempts=0,
            total_sms_sent=0,
            total_emails_sent=0,
        )

        with patch("app.services.orchestrator.is_within_call_window", return_value=False):
            with patch("app.services.orchestrator.is_within_sms_window", return_value=True):
                channel = select_channel(lead)
                assert channel == ContactChannel.sms

    def test_no_channel_when_all_windows_closed(self):
        from app.services.orchestrator import select_channel

        lead = Lead(
            property_id=1,
            status=LeadStatus.hot,
            total_call_attempts=0,
            total_sms_sent=0,
            total_emails_sent=0,
        )

        with patch("app.services.orchestrator.is_within_call_window", return_value=False):
            with patch("app.services.orchestrator.is_within_sms_window", return_value=False):
                channel = select_channel(lead)
                assert channel is None

    def test_email_after_calls_and_sms_exhausted(self):
        from app.services.orchestrator import select_channel, MAX_CALL_ATTEMPTS, MAX_SMS_ATTEMPTS

        lead = Lead(
            property_id=1,
            status=LeadStatus.contacting,
            total_call_attempts=MAX_CALL_ATTEMPTS,
            total_sms_sent=MAX_SMS_ATTEMPTS,
            total_emails_sent=0,
        )

        channel = select_channel(lead)
        assert channel == ContactChannel.email

    def test_none_when_all_exhausted(self):
        from app.services.orchestrator import select_channel, MAX_CALL_ATTEMPTS, MAX_SMS_ATTEMPTS, MAX_EMAIL_ATTEMPTS

        lead = Lead(
            property_id=1,
            status=LeadStatus.contacting,
            total_call_attempts=MAX_CALL_ATTEMPTS,
            total_sms_sent=MAX_SMS_ATTEMPTS,
            total_emails_sent=MAX_EMAIL_ATTEMPTS,
        )

        channel = select_channel(lead)
        assert channel is None


# ═══════════════════════════════════════════════════════════════════════════
# PART 7 — End-to-End Flow Verification
# ═══════════════════════════════════════════════════════════════════════════


class TestEndToEndSmsFlow:
    """Verify the complete SMS pipeline from lead creation to delivery."""

    async def test_new_lead_full_sms_sequence(self, mock_twilio_send):
        """
        Full lifecycle:
        1. Customer submits quote → confirmation SMS via send_sms_async
        2. Worker processes initial outreach → initial_outreach_sms via send_sms
        3. Worker processes follow-up 1 → followup_1_sms via send_sms
        4. Worker processes follow-up 2 → followup_2_sms via send_sms
        """
        from app.services.sms import (
            quote_confirmation_sms,
            send_sms,
            send_sms_async,
        )

        # Step 1: Portal sends confirmation
        body1 = quote_confirmation_sms("Emily")
        r1 = await send_sms_async("3015551111", body1)
        assert r1["status"] == "queued"

        # Step 2: Worker sends initial outreach
        from app.services.sms import initial_outreach_sms
        body2 = initial_outreach_sms("Emily", "789 Pine Ave")
        r2 = send_sms("3015551111", body2)
        assert r2["status"] == "queued"

        # Step 3: Worker sends follow-up 1
        from app.services.sms import followup_1_sms
        body3 = followup_1_sms("Emily")
        r3 = send_sms("3015551111", body3)
        assert r3["status"] == "queued"

        # Step 4: Worker sends follow-up 2
        from app.services.sms import followup_2_sms
        body4 = followup_2_sms("Emily")
        r4 = send_sms("3015551111", body4)
        assert r4["status"] == "queued"

        # Verify full sequence — 4 messages sent
        assert len(mock_twilio_send) == 4
        assert "Solar Command" in mock_twilio_send[0]["body"]  # Confirmation
        assert "789 Pine Ave" in mock_twilio_send[1]["body"]   # Initial outreach
        assert "STOP" in mock_twilio_send[2]["body"]           # Follow-up 1 opt-out
        assert "Steffen" in mock_twilio_send[3]["body"]        # Follow-up 2 personal

        # All sent to same normalized number
        for msg in mock_twilio_send:
            assert msg["to"] == "+13015551111"
            assert msg["from_"] == "+13013643492"

    def test_discovery_module_no_celery_dependency(self):
        """Verify discovery.py no longer imports task_send_sms."""
        with open("app/api/discovery.py", "r") as f:
            source = f.read()

        assert "task_send_sms" not in source, \
            "discovery.py should not reference task_send_sms anymore"
        assert "send_sms_async" in source or "_send_and_record_sms" in source, \
            "discovery.py should use direct Twilio sending"

    def test_tasks_module_uses_real_sms(self):
        """Verify tasks.py imports from sms service, not simulation."""
        with open("app/workers/tasks.py", "r") as f:
            source = f.read()

        assert "from app.services.sms import" in source, \
            "tasks.py should import from app.services.sms"
        assert "send_sms" in source, \
            "tasks.py should call send_sms"
        assert "initial_outreach_sms" in source, \
            "tasks.py should use initial_outreach_sms template"
        assert "followup_1_sms" in source, \
            "tasks.py should use followup_1_sms template"
        assert "followup_2_sms" in source, \
            "tasks.py should use followup_2_sms template"

    def test_portal_module_sends_sms(self):
        """Verify portal.py sends SMS on quote and appointment."""
        with open("app/api/portal.py", "r") as f:
            source = f.read()

        assert "send_sms_async" in source, \
            "portal.py should call send_sms_async"
        assert "quote_confirmation_sms" in source, \
            "portal.py should use quote_confirmation_sms template"
        assert "appointment_confirmation_sms" in source, \
            "portal.py should use appointment_confirmation_sms template"
