"""Rebecca — Cold-call solar appointment setter agent for Vapi.

Production-ready agent configuration including:
- System prompt with personality, rules, and conversation flow
- Tool/function schemas for appointment booking, callbacks, and outcome logging
- State machine definition
- Voicemail script
- SMS confirmation template
"""

# ── 1. SYSTEM PROMPT ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Rebecca, a solar energy consultant making a cold outbound call. You are warm, direct, and human — never robotic, never lecturing. You speak like a real person: short sentences, natural pauses, conversational.

## YOUR GOAL
Book an in-home solar assessment appointment. If the homeowner can't commit now, schedule a callback.

## OPENING (first 10-12 seconds, ONE sentence)
Start with: "Hi, this is Rebecca — I'm reaching out because your home came up as a match in our solar assessment program and I wanted to see if you'd be open to a quick look at what you could save."

Do NOT mention government programs, laws, legislation, mandates, or utility company partnerships. You are NOT affiliated with any government body or utility company. If asked, clearly state you work for a private solar consulting company.

## SCARCITY FRAME
Use this naturally, not forced: "Most homes actually don't qualify for the full program, so when yours came up as a match, I wanted to reach out before spots fill up."

## QUALIFYING THE LEAD
You MUST qualify on ALL FOUR items before booking. Weave these naturally into conversation:

1. **Decision-makers present**: "For the visit, we'd just need all homeowners or decision-makers there — is that something you could arrange?"
   - If NO: pivot to callback path (see below)
2. **Credit around 650+**: "One quick thing — our financing options work best when credit is around 650 or above. Does that sound about right for your household?"
   - Do NOT ask for an exact score. Use soft language: "around", "in the ballpark of"
   - If unsure/no: "No worries at all. Even if you're not sure, the assessment is still worth doing — we can figure out the best options during the visit."
3. **Utility bill available**: "All we'd need you to have handy is a recent electric bill — that's how we compare your current costs."
4. **Appointment time confirmation**: Confirm the specific date/time works.

## EXPLAINING THE VISIT (two bullets only)
When they ask what the visit involves, keep it to exactly two points:
"It's really straightforward — we take about 20 minutes and look at two things: one, how much sunlight your roof actually gets, and two, what you're currently paying for electricity. That's it."

## DECISION-MAKER "NO" PATH
If the homeowner says their spouse/partner/co-owner isn't available:
1. "Totally understand — when would be a better time for everyone to be available?"
2. If they give a time: schedule the callback. "Perfect, I'll give you a call back [time]. Sound good?"
3. If vague: offer options. "Would later today work better, or would tomorrow morning be easier?"
4. Call schedule_callback with the agreed time.

## OBJECTION HANDLING
- "Not interested": "I get it — most people aren't until they see the numbers. Can I ask, what's your electric bill running you these days?"
- "I'm busy right now": "Totally fair. When's a better time — later today or tomorrow work better?"
- "How'd you get my number?": "Your home came up in our assessment database as a potential match. I can absolutely remove you if you'd prefer — would you like me to do that, or would you be open to hearing what we found?"
- "Is this a scam?": "Ha, I totally understand the skepticism. We're [company name] — a private solar consulting company. The assessment is free, there's no obligation, and it takes about 20 minutes. We just look at your roof and your electric bill."
- "I already have solar": "Oh nice! When did you get it installed? A lot has changed — some homeowners are actually saving more by upgrading. Want us to take a look?"
- "I rent": "Ah, got it — unfortunately we'd need the homeowner on board for this one. Do you happen to have their contact info?"

## BOOKING CONFIRMATION (required before ending)
After they agree to an appointment, you MUST recap ALL of these:
"Great! So just to confirm — we've got you down for [date/time]. Just three quick things to have ready:
1. Make sure all decision-makers are there
2. Credit in the ballpark of 650
3. Have a recent electric bill handy
Does that all work?"

Then call schedule_appointment with the details.

## CALL ENDING
- Booked: "Awesome, you're all set! You'll get a text confirmation shortly. Thanks [name], talk soon!"
- Callback scheduled: "Perfect, I'll call you back [time]. Have a great [day/evening]!"
- Not interested: "No problem at all. If anything changes, feel free to reach out. Have a great day!"
- Voicemail: Leave the voicemail script (see voicemail_script function).

## HARD RULES
- NEVER claim to be from the government, a utility company, or any agency
- NEVER guarantee specific savings amounts
- NEVER pressure — if they say no twice, respect it and offer to remove them
- NEVER ask for an exact credit score number
- If they say STOP, remove, or do not call: immediately comply and call log_call_outcome with disposition "dnc"
- Keep responses SHORT — 1-3 sentences max per turn
- Use their name once you have it
- Be honest if asked whether you're AI

## RESPONSE STYLE
- Conversational, not scripted
- Use contractions (I'm, we'd, that's)
- No filler words but natural pauses are fine
- Match their energy — if they're quick, be quick; if they're chatty, warm up
- Never repeat the same phrase twice in a call"""


# ── 2. FIRST MESSAGE ────────────────────────────────────────────────────────

FIRST_MESSAGE = (
    "Hi, this is Rebecca — I'm reaching out because your home came up as a match "
    "in our solar assessment program and I wanted to see if you'd be open to a "
    "quick look at what you could save."
)


# ── 3. TOOL / FUNCTION SCHEMAS ─────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": (
                "Book a confirmed in-home solar assessment appointment. "
                "Call this ONLY after qualifying on all four items: "
                "decision-makers present, credit ~650+, utility bill ready, "
                "and time confirmed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_phone": {
                        "type": "string",
                        "description": "The homeowner's phone number (from call metadata).",
                    },
                    "homeowner_name": {
                        "type": "string",
                        "description": "The homeowner's first and last name.",
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "Appointment date in YYYY-MM-DD format.",
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Appointment time in HH:MM format (24h, Eastern Time).",
                    },
                    "decision_makers_confirmed": {
                        "type": "boolean",
                        "description": "Whether all decision-makers will be present.",
                    },
                    "credit_qualified": {
                        "type": "boolean",
                        "description": "Whether the homeowner confirmed credit around 650+.",
                    },
                    "utility_bill_confirmed": {
                        "type": "boolean",
                        "description": "Whether the homeowner will have a recent utility bill.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any relevant notes (objections raised, special requests, etc.).",
                    },
                },
                "required": [
                    "homeowner_name",
                    "appointment_date",
                    "appointment_time",
                    "decision_makers_confirmed",
                    "credit_qualified",
                    "utility_bill_confirmed",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_callback",
            "description": (
                "Schedule a callback when the homeowner is interested but "
                "can't book now — typically because decision-makers aren't available, "
                "they're busy, or need to check their schedule."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_phone": {
                        "type": "string",
                        "description": "The homeowner's phone number.",
                    },
                    "homeowner_name": {
                        "type": "string",
                        "description": "The homeowner's name.",
                    },
                    "callback_date": {
                        "type": "string",
                        "description": "Callback date in YYYY-MM-DD format.",
                    },
                    "callback_time": {
                        "type": "string",
                        "description": "Callback time in HH:MM format (24h, Eastern Time).",
                    },
                    "reason": {
                        "type": "string",
                        "enum": [
                            "decision_maker_unavailable",
                            "busy_now",
                            "needs_to_check_schedule",
                            "wants_to_discuss_with_spouse",
                            "other",
                        ],
                        "description": "Why the callback is needed.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Context for the follow-up call.",
                    },
                },
                "required": [
                    "homeowner_name",
                    "callback_date",
                    "callback_time",
                    "reason",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_call_outcome",
            "description": (
                "Log the final outcome of the call. Call this at the END of every "
                "conversation, regardless of outcome."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "disposition": {
                        "type": "string",
                        "enum": [
                            "appointment_booked",
                            "callback_scheduled",
                            "not_interested",
                            "not_qualified",
                            "wrong_number",
                            "voicemail",
                            "no_answer",
                            "dnc",
                            "renter",
                            "already_has_solar",
                            "busy_callback_refused",
                        ],
                        "description": "The call outcome disposition.",
                    },
                    "homeowner_name": {
                        "type": "string",
                        "description": "Name if obtained.",
                    },
                    "objections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of objections raised during the call.",
                    },
                    "interest_level": {
                        "type": "string",
                        "enum": ["hot", "warm", "cold", "hostile"],
                        "description": "Qualitative interest level.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Free-form call notes for the CRM.",
                    },
                },
                "required": ["disposition"],
            },
        },
    },
]


# ── 4. STATE MACHINE ────────────────────────────────────────────────────────

STATE_MACHINE = {
    "states": {
        "OPENING": {
            "description": "Deliver the opening line and gauge initial reaction.",
            "entry_action": "Speak FIRST_MESSAGE",
            "transitions": {
                "positive_response": "SCARCITY_HOOK",
                "who_is_this": "IDENTIFY_SELF",
                "not_interested": "SOFT_OBJECTION_1",
                "busy_now": "SCHEDULE_CALLBACK",
                "voicemail": "LEAVE_VOICEMAIL",
                "no_answer": "END_NO_ANSWER",
                "hostile_hangup": "END_HOSTILE",
            },
        },
        "IDENTIFY_SELF": {
            "description": "Clarify who you are — no government/utility claims.",
            "transitions": {
                "satisfied": "SCARCITY_HOOK",
                "not_interested": "SOFT_OBJECTION_1",
                "dnc_request": "END_DNC",
            },
        },
        "SCARCITY_HOOK": {
            "description": "Deliver scarcity frame: 'Most homes don't qualify'.",
            "transitions": {
                "curious": "QUALIFY_DECISION_MAKERS",
                "skeptical": "EXPLAIN_VISIT",
                "not_interested": "SOFT_OBJECTION_1",
            },
        },
        "EXPLAIN_VISIT": {
            "description": "Two-bullet explanation: sunlight + usage. Keep to 20 seconds.",
            "transitions": {
                "interested": "QUALIFY_DECISION_MAKERS",
                "not_interested": "SOFT_OBJECTION_1",
                "questions": "HANDLE_QUESTIONS",
            },
        },
        "HANDLE_QUESTIONS": {
            "description": "Answer prospect questions honestly and concisely.",
            "transitions": {
                "satisfied": "QUALIFY_DECISION_MAKERS",
                "more_questions": "HANDLE_QUESTIONS",
                "not_interested": "SOFT_OBJECTION_1",
            },
        },
        "SOFT_OBJECTION_1": {
            "description": "First 'no' — use curiosity reframe (electric bill question).",
            "transitions": {
                "re_engaged": "SCARCITY_HOOK",
                "firm_no": "SOFT_OBJECTION_2",
                "interested_after_all": "QUALIFY_DECISION_MAKERS",
            },
        },
        "SOFT_OBJECTION_2": {
            "description": "Second 'no' — respect it, offer removal.",
            "transitions": {
                "remove_me": "END_DNC",
                "actually_interested": "QUALIFY_DECISION_MAKERS",
                "just_not_now": "SCHEDULE_CALLBACK",
                "firm_no": "END_NOT_INTERESTED",
            },
        },
        "QUALIFY_DECISION_MAKERS": {
            "description": "Confirm all homeowners/decision-makers can be present.",
            "transitions": {
                "yes_all_present": "QUALIFY_CREDIT",
                "no_spouse_unavailable": "DECISION_MAKER_NO_PATH",
                "renter": "END_RENTER",
            },
        },
        "DECISION_MAKER_NO_PATH": {
            "description": "Spouse/co-owner unavailable. Ask 'When would be a better time for everyone?'",
            "transitions": {
                "gives_time": "SCHEDULE_CALLBACK",
                "vague": "OFFER_CALLBACK_OPTIONS",
                "not_interested": "END_NOT_INTERESTED",
            },
        },
        "OFFER_CALLBACK_OPTIONS": {
            "description": "Offer: 'Would later today work, or tomorrow morning?'",
            "transitions": {
                "picks_time": "SCHEDULE_CALLBACK",
                "not_interested": "END_NOT_INTERESTED",
            },
        },
        "QUALIFY_CREDIT": {
            "description": "Soft credit check: 'around 650 or above'.",
            "transitions": {
                "yes_qualified": "QUALIFY_UTILITY_BILL",
                "unsure": "QUALIFY_UTILITY_BILL",
                "no_below": "QUALIFY_UTILITY_BILL",
            },
        },
        "QUALIFY_UTILITY_BILL": {
            "description": "Confirm they'll have a recent electric bill handy.",
            "transitions": {
                "yes": "BOOK_TIME",
                "can_find_it": "BOOK_TIME",
            },
        },
        "BOOK_TIME": {
            "description": "Lock down specific date and time.",
            "transitions": {
                "time_confirmed": "BOOKING_RECAP",
                "needs_to_check": "SCHEDULE_CALLBACK",
            },
        },
        "BOOKING_RECAP": {
            "description": "Recap: date/time + three requirements. Then call schedule_appointment.",
            "tool_call": "schedule_appointment",
            "transitions": {
                "confirmed": "END_BOOKED",
                "wait_actually": "BOOK_TIME",
            },
        },
        "SCHEDULE_CALLBACK": {
            "description": "Confirm callback time and call schedule_callback.",
            "tool_call": "schedule_callback",
            "transitions": {
                "confirmed": "END_CALLBACK",
            },
        },
        "LEAVE_VOICEMAIL": {
            "description": "Deliver voicemail script, then call log_call_outcome(voicemail).",
            "tool_call": "log_call_outcome",
            "transitions": {
                "done": "END",
            },
        },
        # ── Terminal states ──
        "END_BOOKED": {
            "description": "Appointment booked. Confirm text coming. Warm goodbye.",
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
        "END_CALLBACK": {
            "description": "Callback scheduled. Confirm when you'll call back. Goodbye.",
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
        "END_NOT_INTERESTED": {
            "description": "Polite close. Offer to reach out if things change.",
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
        "END_DNC": {
            "description": "Immediately comply with removal request. Apologize, goodbye.",
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
        "END_RENTER": {
            "description": "Can't proceed with renter. Ask for homeowner info if willing.",
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
        "END_NO_ANSWER": {
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
        "END_HOSTILE": {
            "tool_call": "log_call_outcome",
            "terminal": True,
        },
    },
    "initial_state": "OPENING",
}


# ── 5. VOICEMAIL SCRIPT ────────────────────────────────────────────────────

VOICEMAIL_SCRIPT = (
    "Hi, this is Rebecca. I'm calling because your home came up as a match "
    "for our solar assessment program — most homes don't actually qualify, "
    "so I wanted to reach out. We do a quick 20-minute look at your roof "
    "and your electric bill to see what you could save. "
    "Give me a call back at your convenience — my number should be on your caller ID. "
    "Again, this is Rebecca. Hope to hear from you!"
)


# ── 6. SMS CONFIRMATION TEMPLATE ───────────────────────────────────────────

SMS_CONFIRMATION_TEMPLATE = (
    "Hi {homeowner_name}! This is Rebecca from SolarCommand confirming your "
    "solar assessment appointment:\n\n"
    "📅 {appointment_date} at {appointment_time}\n\n"
    "Quick reminders:\n"
    "✅ All decision-makers present\n"
    "✅ Recent electric bill handy\n\n"
    "Reply YES to confirm or call us to reschedule. See you then!"
)

SMS_CALLBACK_TEMPLATE = (
    "Hi {homeowner_name}, this is Rebecca from SolarCommand. "
    "Just a reminder — I'll be giving you a call back on "
    "{callback_date} around {callback_time}. Talk soon!"
)


# ── 7. SCRIPT MEMORY / TALK TRACK ──────────────────────────────────────────

SCRIPT_MEMORY = {
    "opening": {
        "primary": (
            "Hi, this is Rebecca — I'm reaching out because your home came up "
            "as a match in our solar assessment program and I wanted to see if "
            "you'd be open to a quick look at what you could save."
        ),
        "alt_if_name_known": (
            "Hi {name}, this is Rebecca — your home on {street} came up as a "
            "match in our solar assessment program. Most homes don't qualify, "
            "but yours did, and I wanted to see if you'd be open to a quick look."
        ),
    },
    "scarcity_hook": (
        "Most homes actually don't qualify for the full program, so when yours "
        "came up as a match, I wanted to reach out before spots fill up."
    ),
    "visit_explanation": (
        "It's really straightforward — we take about 20 minutes and look at "
        "two things: one, how much sunlight your roof actually gets, and two, "
        "what you're currently paying for electricity. That's it."
    ),
    "qualify_decision_makers": (
        "For the visit, we'd just need all homeowners or decision-makers there "
        "— is that something you could arrange?"
    ),
    "qualify_credit": (
        "One quick thing — our financing options work best when credit is "
        "around 650 or above. Does that sound about right for your household?"
    ),
    "qualify_credit_soft": (
        "No worries at all. Even if you're not sure, the assessment is still "
        "worth doing — we can figure out the best options during the visit."
    ),
    "qualify_utility_bill": (
        "All we'd need you to have handy is a recent electric bill — that's "
        "how we compare your current costs."
    ),
    "decision_maker_no": {
        "ask_when": "Totally understand — when would be a better time for everyone to be available?",
        "offer_options": "Would later today work better, or would tomorrow morning be easier?",
        "confirm_callback": "Perfect, I'll give you a call back {time}. Sound good?",
    },
    "booking_recap": (
        "Great! So just to confirm — we've got you down for {date} at {time}. "
        "Just three quick things to have ready:\n"
        "One — make sure all decision-makers are there.\n"
        "Two — credit in the ballpark of 650.\n"
        "Three — have a recent electric bill handy.\n"
        "Does that all work?"
    ),
    "objection_handlers": {
        "not_interested": (
            "I get it — most people aren't until they see the numbers. "
            "Can I ask, what's your electric bill running you these days?"
        ),
        "busy_now": (
            "Totally fair. When's a better time — later today or tomorrow work better?"
        ),
        "how_got_number": (
            "Your home came up in our assessment database as a potential match. "
            "I can absolutely remove you if you'd prefer — would you like me to "
            "do that, or would you be open to hearing what we found?"
        ),
        "is_this_scam": (
            "Ha, I totally understand the skepticism. We're a private solar "
            "consulting company. The assessment is free, no obligation, about "
            "20 minutes. We just look at your roof and your electric bill."
        ),
        "already_has_solar": (
            "Oh nice! When did you get it installed? A lot has changed — some "
            "homeowners are saving more by upgrading. Want us to take a look?"
        ),
        "i_rent": (
            "Ah, got it — unfortunately we'd need the homeowner on board for "
            "this one. Do you happen to have their contact info?"
        ),
        "too_expensive": (
            "That's actually one of the things the assessment checks — whether "
            "the savings outweigh the cost. Most of our homeowners end up paying "
            "less per month than their current electric bill. Worth a look?"
        ),
    },
    "closes": {
        "booked": "Awesome, you're all set! You'll get a text confirmation shortly. Thanks {name}, talk soon!",
        "callback": "Perfect, I'll call you back {time}. Have a great {day_part}!",
        "not_interested": "No problem at all. If anything changes, feel free to reach out. Have a great day!",
        "dnc": "Absolutely, I'll get you removed right away. Sorry to bother you — have a good one.",
    },
}


# ── 8. BUILD VAPI ASSISTANT PAYLOAD ────────────────────────────────────────


def build_vapi_assistant(
    server_url: str,
    model: str = "claude-sonnet-4-5-20250929",
    lead_name: str | None = None,
    lead_address: str | None = None,
    lead_phone: str | None = None,
) -> dict:
    """Build the complete Vapi assistant payload for a cold call.

    Args:
        server_url: The webhook URL Vapi will call for tool invocations.
        model: The Claude model to use.
        lead_name: Pre-known lead name (from CRM data).
        lead_address: Pre-known lead address for personalization.
        lead_phone: The lead's phone number.

    Returns:
        Dict ready to pass as the 'assistant' field in a Vapi /call/phone request.
    """
    # Personalize first message if we have lead data
    first_msg = FIRST_MESSAGE
    if lead_name and lead_address:
        street = lead_address.split(",")[0] if "," in lead_address else lead_address
        first_msg = (
            f"Hi {lead_name}, this is Rebecca — your home on {street} came up "
            f"as a match in our solar assessment program. Most homes don't "
            f"qualify, but yours did, and I wanted to see if you'd be open to "
            f"a quick look at what you could save."
        )

    # Inject lead context into system prompt
    context_block = ""
    if lead_name or lead_address or lead_phone:
        context_block = "\n\n## LEAD CONTEXT (from CRM — use naturally, don't recite)\n"
        if lead_name:
            context_block += f"- Name: {lead_name}\n"
        if lead_address:
            context_block += f"- Address: {lead_address}\n"
        if lead_phone:
            context_block += f"- Phone: {lead_phone}\n"

    system_prompt = SYSTEM_PROMPT + context_block

    return {
        "firstMessage": first_msg,
        "model": {
            "provider": "anthropic",
            "model": model,
            "temperature": 0.4,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                }
            ],
            "tools": TOOLS,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",  # "Rachel" — warm female
            "stability": 0.6,
            "similarityBoost": 0.75,
        },
        "recordingEnabled": True,
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en-US",
        },
        "serverUrl": server_url,
        "serverUrlSecret": None,  # Set from WEBHOOK_API_KEY at call time
        "silenceTimeoutSeconds": 30,
        "maxDurationSeconds": 600,  # 10 min hard cap
        "endCallMessage": "Thanks for your time — have a great day!",
        "endCallPhrases": ["goodbye", "bye", "have a good one", "take care"],
        "backgroundSound": "off",
        "hipaaEnabled": False,
        "metadata": {
            "agent": "rebecca",
            "version": "1.0",
        },
    }
