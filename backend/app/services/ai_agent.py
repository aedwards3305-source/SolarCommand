"""AI voice/SMS agent logic — LLM integration stub for MVP."""

# In production, this module integrates with OpenAI function-calling
# and Twilio's programmable voice. For MVP, it provides the interface
# and a simulation mode.

SYSTEM_PROMPT = """You are Sarah, a friendly solar energy consultant calling on behalf of
{company_name} Solar. You are calling {owner_name} about their home at {address}.

RULES (NEVER VIOLATE):
1. Identify yourself and the company within 10 seconds.
2. Disclose that the call may be recorded.
3. Ask "Is now a good time?" before proceeding.
4. If they say stop/remove/don't call → thank them, confirm removal, end call.
5. Never guarantee specific savings amounts.
6. Never claim government mandates.
7. If asked if you're a robot/AI, answer honestly.
8. Be warm, neighborly, and concise.

QUALIFICATION QUESTIONS:
1. Confirm homeownership at the address.
2. Ask about prior solar interest.
3. Ask about monthly electric bill range.
4. Ask about roof condition.

BOOKING:
If qualified, offer morning or afternoon appointment options.
Confirm date, time, and that a solar specialist will visit — no obligation.

TOOLS AVAILABLE:
- lookup_property(lead_id) → property details
- update_lead_status(lead_id, status, reason)
- book_appointment(lead_id, rep_id, datetime, notes)
- log_consent(lead_id, consent_type, channel, status)
- send_sms(lead_id, template_id, personalization)
- schedule_callback(lead_id, datetime)
- add_note(lead_id, content)
- end_call(lead_id, disposition)
"""


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_property",
            "description": "Fetch property details for the current lead",
            "parameters": {
                "type": "object",
                "properties": {"lead_id": {"type": "integer"}},
                "required": ["lead_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead_status",
            "description": "Update the lead status in CRM",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "status": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["lead_id", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a consultation appointment with a closer rep",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "rep_id": {"type": "integer"},
                    "datetime": {"type": "string", "format": "date-time"},
                    "notes": {"type": "string"},
                },
                "required": ["lead_id", "rep_id", "datetime"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_consent",
            "description": "Log a consent event (opt-in or opt-out)",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "consent_type": {
                        "type": "string",
                        "enum": ["voice_call", "sms", "email", "all_channels"],
                    },
                    "channel": {"type": "string", "enum": ["voice", "sms", "email"]},
                    "status": {
                        "type": "string",
                        "enum": ["opted_in", "opted_out"],
                    },
                },
                "required": ["lead_id", "consent_type", "channel", "status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "end_call",
            "description": "End the current call with a disposition",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "integer"},
                    "disposition": {
                        "type": "string",
                        "enum": [
                            "appointment_booked",
                            "callback_scheduled",
                            "interested_not_ready",
                            "not_interested",
                            "not_homeowner",
                            "wrong_number",
                            "voicemail",
                            "no_answer",
                            "do_not_call",
                        ],
                    },
                },
                "required": ["lead_id", "disposition"],
            },
        },
    },
]


def build_system_prompt(
    company_name: str, owner_name: str, address: str
) -> str:
    """Build the system prompt with lead-specific context."""
    return SYSTEM_PROMPT.format(
        company_name=company_name,
        owner_name=owner_name,
        address=address,
    )
