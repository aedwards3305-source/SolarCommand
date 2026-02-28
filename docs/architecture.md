# SolarCommand Architecture

## System Overview

SolarCommand is a full-stack AI-powered lead intelligence and outreach platform for residential
solar companies. It combines property data scoring, AI-driven multi-channel outreach (voice,
SMS, email), and compliance automation into a single platform.

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS | Responsive SPA with server components |
| API | FastAPI (Python 3.11+), async | REST API with JWT auth, RBAC |
| Database | PostgreSQL 16 | 22 tables, full audit trail |
| Cache/Queue | Redis 7 | Celery broker, result backend, caching |
| Task Queue | Celery + Beat | Async processing, scheduled jobs |
| AI Engine | Anthropic Claude (Sonnet 4.5) | SMS classification, QA, NBA, briefs |
| Voice | Twilio / Vapi (pluggable) | Outbound calls, recording, transcription |
| Enrichment | People Data Labs, Melissa | Contact discovery, phone/email validation |
| Infrastructure | Docker Compose | Single-command deployment |

---

## Architecture Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js 14    │────▶│   FastAPI API     │────▶│  PostgreSQL 16  │
│   (Frontend)    │     │   (8000)          │     │  (22 tables)    │
│   Port 3000     │     │                   │     │                 │
└─────────────────┘     │  JWT Auth + RBAC  │     └─────────────────┘
                        │  38+ API Routes   │              │
                        └──────┬───────────┘              │
                               │                           │
                        ┌──────▼───────────┐     ┌────────▼────────┐
                        │   Redis 7        │     │  Celery Worker  │
                        │   (Queue/Cache)  │◀───▶│  + Beat         │
                        │                  │     │  7 scheduled    │
                        └──────────────────┘     │  jobs           │
                                                  └────────┬────────┘
                                                           │
                        ┌──────────────────────────────────┼──────────────┐
                        │                                  │              │
                 ┌──────▼──────┐   ┌──────────────┐  ┌────▼─────┐  ┌────▼─────┐
                 │  Anthropic  │   │  Twilio/Vapi  │  │   PDL    │  │ Melissa  │
                 │  Claude API │   │  Voice API    │  │  Enrich  │  │ Validate │
                 └─────────────┘   └──────────────┘  └──────────┘  └──────────┘
```

---

## Data Model (22 Tables)

### Core CRM
- **property** — Property data, solar factors, owner info
- **lead** — Lead lifecycle, scoring tier, outreach tracking
- **lead_score** — 10-factor scoring with explainability
- **outreach_attempt** — Multi-channel outreach history
- **appointment** — Booking with status tracking
- **rep_user** — Sales reps with RBAC (admin/rep/ops)

### Communication
- **inbound_message** — SMS thread with AI classification
- **conversation_transcript** — Call transcripts with AI summaries + voice provider fields
- **script_version** — Versioned outreach scripts
- **script_experiment** — A/B testing for scripts

### AI Operator
- **ai_run** — Full audit trail for every AI call (tokens, cost, latency, I/O)
- **ai_memory** — Durable learning store (lessons, patterns, per-county/rep insights)
- **nba_decision** — Next Best Action recommendations with confidence + TTL
- **qa_review** — Compliance QA with flags and scoring
- **objection_tag** — Extracted objections with evidence spans

### Enrichment
- **contact_enrichment** — PDL enrichment (emails, phones, LinkedIn, job title)
- **contact_validation** — Melissa validation (phone/email/address validity)
- **contact_intelligence** — Aggregated best-contact-time + validation

### Compliance & Security
- **consent_log** — Opt-in/opt-out with evidence chain
- **audit_log** — Every system action logged (actor, entity, old/new values)
- **note** — Manual and AI-generated notes

---

## AI Operator Module

The AI Operator is SolarCommand's autonomous intelligence layer. Every AI call:

1. **Runs through ClaudeClient** — unified interface with cost tracking
2. **Logs to ai_run** — full input/output, tokens, cost, latency (audit trail)
3. **Falls back deterministically** — safe, schema-compliant defaults when Claude is unavailable
4. **Respects safety gates** — `ai_allow_auto_actions=False` means suggest-only, human-approved

### AI Tasks
| Task | Trigger | Output |
|------|---------|--------|
| SMS Classification | Inbound SMS webhook | Intent, suggested reply, actions |
| Transcript Summary | Call completion | Summary, sentiment |
| QA Review | Call/SMS completion | Compliance score, flags |
| Objection Extraction | Transcript analysis | Tags with confidence + evidence |
| Next Best Action | Nightly batch + on-demand | Action, channel, schedule, reasons |
| Rep Brief | On-demand | Talk track, objection handlers, approach |
| Script Suggestions | Weekly + on-demand | Edits, hypotheses, expected lift |
| Weekly Insights | Monday 7am ET | Narrative, drivers, recommendations |
| Memory Update | Weekly | Lessons, patterns (fed back into prompts) |

### Safety by Design
- `AI_ALLOW_AUTO_ACTIONS=false` — AI suggests, humans approve
- `SMS_AUTO_REPLY_ENABLED=false` — No auto-send without explicit opt-in
- Opt-out keywords detected instantly, lead moved to DNC
- Quiet hours enforced (Mon-Fri 9a-9p, Sat 10a-5p, no Sunday)
- All consent changes logged with evidence chain

---

## Voice Architecture

```
Lead Detail → "Voice Call" button
     │
     ▼
task_place_voice_call (Celery)
     │
     ├── Safety gates (DNC, consent, quiet hours)
     ├── Get script from script_version table
     │
     ▼
VoiceProvider.place_call() ← Provider-agnostic interface
     │
     ├── TwilioVoiceProvider (Programmable Voice)
     └── VapiVoiceProvider (AI-driven conversations)
     │
     ▼
Webhooks: /webhooks/voice/status, /webhooks/voice/recording
     │
     ▼
task_process_call_completion (Celery)
     │
     ├── Fetch recording URL + transcript
     ├── Update conversation_transcript
     │
     ▼
AI Pipeline: summary → QA review → objection extraction → NBA update
```

---

## Enrichment Pipeline

```
Hot/Warm Lead (scored or on-demand)
     │
     ▼
task_enrich_contact (Celery)
     │
     ├── PDL: person enrichment (emails, phones, job, LinkedIn)
     ├── Confidence threshold gate (default 0.5)
     │
     ▼
task_validate_contact (Celery)
     │
     ├── Melissa: phone validation (valid, type, carrier, line status)
     ├── Melissa: email validation (valid, deliverable, disposable)
     ├── Melissa: address validation (valid, USPS deliverable)
     │
     ▼
ContactIntelligence updated → feeds into scoring + NBA context
```

---

## Deployment

```bash
# Single command deployment
docker compose up -d

# Services: db, redis, api, worker, frontend
# Migrations run automatically on api startup
# Seed data loads on first boot
```

### Required Environment Variables
See `.env.example` for the full list. Key ones:
- `ANTHROPIC_API_KEY` — Claude AI (required for AI features)
- `TWILIO_*` — Voice + SMS (required for outreach)
- `PDL_API_KEY` — Contact enrichment (optional)
- `MELISSA_API_KEY` — Contact validation (optional)
