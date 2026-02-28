"""Tests for prompt template rendering."""

from app.services.prompts import (
    NBA_USER,
    QA_REVIEW_USER,
    SMS_AGENT_USER,
    render_template,
)


def test_render_template_basic():
    template = "Hello {{name}}, welcome to {{company}}!"
    result = render_template(template, name="Alice", company="SolarCo")
    assert result == "Hello Alice, welcome to SolarCo!"


def test_render_template_missing_key():
    """Missing keys should stay as placeholders (not crash)."""
    template = "Hello {{name}}, your score is {{score}}."
    result = render_template(template, name="Bob")
    assert "Bob" in result
    assert "{{score}}" in result


def test_render_template_no_vars():
    template = "Static text with no placeholders."
    assert render_template(template) == template


def test_sms_agent_user_template():
    result = render_template(
        SMS_AGENT_USER,
        lead_name="John Smith",
        lead_status="new",
        lead_score="85",
        address="123 Oak St",
        county="Anne Arundel",
        message_count="3",
        from_number="+14105551234",
        message_body="Yes I'm interested",
    )
    assert "John Smith" in result
    assert "Yes I'm interested" in result


def test_qa_review_user_template():
    result = render_template(
        QA_REVIEW_USER,
        channel="sms",
        lead_name="Jane Doe",
        lead_id="42",
        timestamp="2024-01-01T12:00:00",
        transcript="Rep: Hi there\nLead: Hello",
    )
    assert "Jane Doe" in result
    assert "sms" in result


def test_nba_user_template():
    result = render_template(
        NBA_USER,
        lead_id="1",
        lead_name="Test Lead",
        lead_status="contacted",
        lead_score="60",
        phone_type="mobile",
        best_call_hour="14",
        call_attempts="2",
        sms_sent="1",
        emails_sent="0",
        last_contacted="2024-01-01T12:00:00",
        is_dnc="no",
        consent_status="opted_in",
        current_time_et="10:00",
    )
    assert "Test Lead" in result
    assert "contacted" in result
