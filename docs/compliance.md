# SolarCommand Compliance & Safety

## Overview

SolarCommand is designed with compliance as a first-class architectural concern, not an
afterthought. Every outreach decision passes through multiple safety gates before execution.

---

## TCPA Compliance

### Consent Management
- **Consent logging** — Every consent event (opt-in, opt-out, revocation) is logged with:
  - Timestamp
  - Channel (voice, SMS, email)
  - Evidence type (verbal, SMS reply, web form, written)
  - Evidence URL (recording, screenshot)
  - IP address and user agent (for web forms)

### Opt-Out Detection
SolarCommand automatically detects opt-out intent from inbound messages:

**Detected keywords:** STOP, unsubscribe, cancel, end, quit, opt out, optout, opt-out,
remove me, do not contact, don't contact, leave me alone

When detected:
1. Lead status immediately changes to DNC
2. Consent log entry created (opted_out)
3. All future outreach blocked
4. Audit log entry created

### Quiet Hours
Outreach is only allowed during:
- **Monday-Friday:** 9:00 AM - 9:00 PM ET
- **Saturday:** 10:00 AM - 5:00 PM ET
- **Sunday:** No contact

### DNC List
Leads in DNC status cannot be contacted through any channel. The system checks DNC status
before every outreach attempt.

---

## AI Safety

### Suggest-Only Mode (Default)
`AI_ALLOW_AUTO_ACTIONS=false` — This is the default and recommended production setting.

When false:
- AI classifies messages but does NOT auto-send replies
- AI recommends next best actions but does NOT auto-execute
- All AI suggestions are presented to humans for approval
- Reps must explicitly approve and send any outreach

### SMS Auto-Reply
`SMS_AUTO_REPLY_ENABLED=false` — Additional safety gate for SMS.

Even if auto-actions are enabled, SMS auto-reply has its own separate toggle.

### Deterministic Fallbacks
When the AI provider is unavailable (API down, key expired, rate limited):
- Every task type returns a safe, deterministic fallback
- Fallbacks match expected schemas exactly
- NBA defaults to "wait" with 0.0 confidence
- QA defaults to 70 compliance score with checklist pass
- SMS classification defaults to "unknown" intent with `requires_human=true`

---

## Voice Call Compliance

### Pre-Call Gates
Before any outbound call:
1. Lead status checked (not DNC, not terminal, not disqualified)
2. Consent status checked (no opt-out records)
3. Quiet hours checked (within allowed window)
4. Phone number exists

### During Call
- Disclosure played automatically at call start
- Call recorded with proper notice
- Recording stored securely

### Post-Call
- Transcript analyzed for compliance (QA review)
- Objections extracted and logged
- Recording URL stored in conversation record
- Full audit trail maintained

---

## Audit Trail

Every action in SolarCommand is logged:

### audit_log table
- **actor** — Who performed the action (system, ai_agent, user email)
- **action** — What happened (lead.status_change, sms.inbound, voice.call_placed)
- **entity_type** — What was affected (lead, property, appointment)
- **entity_id** — Which record
- **old_value** / **new_value** — Before/after state
- **metadata_json** — Additional context
- **created_at** — When it happened

### ai_run table
Every AI API call is logged with:
- Task type
- Model and temperature used
- Full input and output JSON
- Token count (input + output)
- Cost in USD
- Latency in milliseconds
- Status (success/error)
- Input hash (for reproducibility verification)

---

## Data Protection

### Sensitive Data Handling
- API keys stored in environment variables, never in code
- `.env` file is gitignored
- Database credentials use Docker Compose secrets
- JWT tokens expire after 8 hours
- Passwords hashed with bcrypt

### Role-Based Access Control
| Role | Access |
|------|--------|
| Admin | All features, AI runs, audit logs, user management |
| Rep | Lead detail, outreach, appointments, messages |
| Ops | Dashboard, reports, scripts, experiments |

---

## Enrichment Data Compliance

### People Data Labs (PDL)
- Only used for business contact enrichment
- Only enriches Hot/Warm leads (no speculative lookups)
- Confidence threshold gates usage (default 0.5)
- Raw responses stored for audit

### Melissa Data
- Used for contact validation only
- Validates phone deliverability before outreach
- Flags disposable emails
- No PII is shared beyond what's necessary for validation
