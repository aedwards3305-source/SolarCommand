# SolarCommand — System Design Document

---

## A) EXECUTIVE SUMMARY

### What We're Building
SolarCommand is a Lead Intelligence + AI Outreach platform purpose-built for residential solar sales in Maryland. It replaces high-cost door-to-door canvassing with automated prospect identification, AI-powered multi-channel outreach (voice, SMS, email), and a solar-specific CRM that routes warm, qualified leads directly to closers.

### Why It Wins
- **80%+ cost reduction** per qualified lead vs. door knocking (no gas, no idle reps, 24/7 coverage).
- **Data-driven targeting**: public property records + satellite/roof data + utility rates = precise Solar Readiness Scores.
- **Compliance-first**: TCPA consent logging, DNC scrubbing, and full audit trails built into every interaction.
- **Speed to appointment**: AI agent qualifies in real-time, books directly into closer calendars.

### MVP Scope
- **Geography**: Anne Arundel County + Howard County, MD.
- **Channels**: AI voice calls + SMS follow-ups + email nurture.
- **Users**: 1 admin, 2–4 closers using Rep View.
- **Timeline**: 90 days to production MVP.

### Major Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| TCPA violation | Legal/financial | Consent-first architecture, auto DNC scrub, all calls logged |
| Low contact rates | Revenue | Multi-channel cascade (call→SMS→email), optimal time windows |
| Data quality | Bad leads | Multiple data source cross-referencing, confidence scoring |
| AI voice quality | Brand damage | Human-in-the-loop escalation, strict guardrails, call recording |
| Scaling beyond MD | Architecture debt | State-config module from day 1, pluggable data sources |

---

## B) SYSTEM ARCHITECTURE

### High-Level Architecture (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SOLARCOMMAND PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐   │
│  │  DATA INGEST │   │  LEAD SCORE  │   │   OUTREACH ORCHESTRATOR  │   │
│  │              │   │   ENGINE     │   │                          │   │
│  │ • Property   │──▶│ • Heuristic  │──▶│ • Scheduling Engine      │   │
│  │   Records    │   │   v1         │   │ • Channel Selector       │   │
│  │ • Ownership  │   │ • ML v2      │   │ • Retry / Escalation     │   │
│  │ • Parcel     │   │ • Feature    │   │ • DNC / Consent Check    │   │
│  │   Data       │   │   Store      │   │ • Stop Conditions        │   │
│  └──────────────┘   └──────────────┘   └────────┬─────────────────┘   │
│         │                                        │                     │
│         ▼                                        ▼                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐   │
│  │   POSTGRES   │◀──│  REDIS QUEUE │◀──│   AI AGENT LAYER         │   │
│  │              │   │              │   │                          │   │
│  │ • Properties │   │ • Call Jobs  │   │ • Voice Agent (Twilio)   │   │
│  │ • Leads      │   │ • SMS Jobs   │   │ • SMS Agent (Twilio)     │   │
│  │ • Outreach   │   │ • Email Jobs │   │ • Email Agent (SendGrid) │   │
│  │ • Consent    │   │ • Score Jobs │   │ • LLM Brain (OpenAI)     │   │
│  │ • Audit      │   │              │   │ • Tool Calls             │   │
│  └──────┬───────┘   └──────────────┘   └──────────────────────────┘   │
│         │                                                              │
│         ▼                                                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     FASTAPI BACKEND                              │  │
│  │                                                                  │  │
│  │  /leads    /outreach    /appointments    /admin    /analytics    │  │
│  └──────────────────────────┬───────────────────────────────────────┘  │
│                             │                                          │
│                             ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    NEXT.JS FRONTEND                              │  │
│  │                                                                  │  │
│  │  Dashboard │ Lead List │ Lead Detail │ Calendar │ Admin Panel    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow (End-to-End)

```
1. INGEST: Property records (SDAT bulk, API) → normalize → dedupe → store in `property` + `homeowner`
2. SCORE:  Scoring engine reads property features → computes Solar Readiness Score → stores in `lead_score`
3. FILTER: Leads above threshold (score ≥ 40) become active leads → DNC scrub → consent-ready
4. QUEUE:  Outreach Orchestrator selects top leads → creates jobs in Redis queue
5. CALL:   Worker picks job → AI voice agent calls via Twilio → conversation → disposition
6. LOG:    Every touch logged in `outreach_attempt` + `consent_log` + `audit_log`
7. ROUTE:  Qualified leads → book appointment → notify closer → appears in Rep View calendar
8. NURTURE: Non-answers → SMS follow-up (Day 1, 3, 7) → Email nurture (Week 1, 2, 4)
9. CLOSE:  Closer views lead detail, property info, conversation history → visits home → closes deal
```

### Module Descriptions

| Module | Responsibility |
|--------|---------------|
| **Data Ingestion** | Bulk import and API-based property/ownership data loading, normalization, dedup |
| **Scoring Engine** | Compute Solar Readiness Score from property features, store score history |
| **Outreach Orchestrator** | Schedule, sequence, and manage multi-channel outreach with compliance gates |
| **AI Voice Agent** | LLM-driven conversational agent for phone calls via Twilio |
| **CRM Core** | Lead lifecycle management, appointment booking, rep assignment |
| **Analytics** | KPI dashboards, conversion funnels, campaign performance |
| **Admin/Compliance** | Script management, consent viewer, audit log browser, DNC management |

---

## D) LEAD SCORING

### Solar Readiness Score (0–100)

#### Weighted Factors (v1 Heuristics)

| Factor | Weight | Score Range | Source |
|--------|--------|-------------|--------|
| **Roof Age** (years since built/reroof) | 15 | 0–15: <5yr=15, 5-15=12, 15-25=8, >25=3 | Property records |
| **Home Ownership** (owner-occupied) | 15 | Owner-occupied=15, else=0 | Tax records |
| **Roof Area** (sq ft, south-facing) | 15 | >1500=15, 1000-1500=12, 500-1000=8, <500=3 | Parcel data/satellite |
| **Home Value** ($) | 10 | 250k-750k=10, 150-250k=7, >750k=5, <150k=2 | Assessment |
| **Electric Utility Rate** ($/kWh) | 10 | BGE zone=10, other MD=7 | Utility zone map |
| **Tree Cover / Shade** (%) | 10 | <10%=10, 10-25%=7, 25-50%=4, >50%=1 | Satellite/canopy data |
| **Neighborhood Solar Adoption** (%) | 10 | >10%=10, 5-10%=7, 1-5%=4, <1%=1 | Permit data |
| **Income Bracket** (census tract) | 8 | 75k-200k=8, 50-75k=5, >200k=4, <50k=2 | Census ACS |
| **Property Type** (single family) | 5 | SFH=5, Townhome=3, else=0 | Property records |
| **No Existing Solar** | 2 | No panels=2, Has panels=0 | Permit data/satellite |

**Total: 100 points**

#### Scoring Tiers
- **Hot (75–100)**: Immediate outreach, call first
- **Warm (50–74)**: Queue for outreach within 48hrs
- **Cool (25–49)**: Email nurture only
- **Cold (0–24)**: Do not contact, re-score quarterly

#### v1 Pseudocode

```python
def compute_solar_score(property_data: dict) -> int:
    score = 0

    # Roof age
    roof_age = current_year - property_data.get("year_built_or_reroofed", 1970)
    if roof_age < 5:      score += 15
    elif roof_age < 15:   score += 12
    elif roof_age < 25:   score += 8
    else:                  score += 3

    # Ownership
    if property_data.get("owner_occupied", False):
        score += 15

    # Roof area
    roof_sqft = property_data.get("roof_area_sqft", 0)
    if roof_sqft > 1500:    score += 15
    elif roof_sqft > 1000:  score += 12
    elif roof_sqft > 500:   score += 8
    else:                    score += 3

    # Home value
    value = property_data.get("assessed_value", 0)
    if 250_000 <= value <= 750_000:   score += 10
    elif 150_000 <= value < 250_000:  score += 7
    elif value > 750_000:             score += 5
    else:                              score += 2

    # Utility rate zone
    if property_data.get("utility_zone") == "BGE":
        score += 10
    else:
        score += 7

    # Shade
    shade_pct = property_data.get("tree_cover_pct", 50)
    if shade_pct < 10:     score += 10
    elif shade_pct < 25:   score += 7
    elif shade_pct < 50:   score += 4
    else:                   score += 1

    # Neighborhood adoption
    adoption_pct = property_data.get("neighborhood_solar_pct", 0)
    if adoption_pct > 10:    score += 10
    elif adoption_pct > 5:   score += 7
    elif adoption_pct > 1:   score += 4
    else:                     score += 1

    # Income
    income = property_data.get("median_household_income", 0)
    if 75_000 <= income <= 200_000:   score += 8
    elif 50_000 <= income < 75_000:   score += 5
    elif income > 200_000:            score += 4
    else:                              score += 2

    # Property type
    ptype = property_data.get("property_type", "")
    if ptype == "SFH":         score += 5
    elif ptype == "TOWNHOME":  score += 3

    # Existing solar
    if not property_data.get("has_existing_solar", False):
        score += 2

    return min(score, 100)
```

#### v2 ML Plan
- Collect conversion data (lead→appointment→sale) for 6 months.
- Features: all v1 factors + time-of-contact, channel, rep, season, weather.
- Train gradient-boosted model (XGBoost/LightGBM) to predict P(conversion).
- A/B test ML score vs. heuristic score, measure lift.
- Retrain quarterly with new conversion data.

---

## E) AI DIGITAL CALL CENTER DESIGN

### Agent Persona
- **Name**: "Sarah from [Company Name] Solar"
- **Tone**: Friendly, professional, neighborly. Not salesy.
- **Key Behavior**: Always identifies as AI when asked directly. Never lies about being human.

### Compliance Behaviors (Hard Rules)
1. **Opening**: Must identify company name and purpose within first 10 seconds.
2. **Consent**: Must ask "Is now a good time to talk?" before proceeding.
3. **Opt-out**: If prospect says "stop", "remove me", "don't call", "not interested" → immediately thank them, confirm removal, end call.
4. **Do Not Call**: Honor immediately, log to `consent_log` with `status=opted_out`.
5. **Recording Disclosure**: "This call may be recorded for quality purposes" (MD is one-party consent, but disclose anyway).
6. **No False Claims**: Never guarantee savings amounts, never claim government mandates.
7. **Escalation**: If prospect asks for a human, transfer or schedule callback.

### Voice Call Script

```
OPENING (0-15 sec):
"Hi, this is Sarah calling from [Company] Solar. We help homeowners in
[County] save on electricity with solar panels. Is now a good time for
a quick 2-minute chat?"

IF NO → "No problem at all! Would a better time work, or would you prefer
I send some info by text or email instead?"
  → [book_callback] or [send_sms_info] or [mark_not_interested]

IF YES → QUALIFICATION

QUALIFICATION (15-60 sec):
Q1: "Great! Just to confirm, are you the homeowner at [address]?"
  → IF NO → "Oh I'm sorry for the mix-up! Have a great day." [end_call]
  → IF YES → continue

Q2: "Awesome. Have you ever looked into solar for your home before?"
  → Captures: prior_interest (yes/no/considered)

Q3: "What's your typical monthly electric bill, roughly?"
  → Captures: monthly_bill (range buckets: <$100, $100-200, $200-300, $300+)

Q4: "And is your roof in good shape — no major repairs needed soon?"
  → Captures: roof_condition (good/needs_work/unsure)

OBJECTION HANDLING:
- "Too expensive" → "Actually, most of our customers go solar with $0 down
   and payments lower than their current electric bill. Worth a 15-min look?"
- "I'm renting" → "Got it — thanks for letting me know! Have a great day."
   [mark_ineligible]
- "Not interested" → "Totally understand. If you change your mind, we're
   always here. Have a great day!" [mark_not_interested]
- "Is this a scam?" → "Great question! We're [Company], a local Maryland
   solar installer. You can look us up at [website]. Would you like me
   to send you our info by text?"

BOOKING (60-90 sec):
"Based on what you've told me, it sounds like your home could be a great
fit. We have a solar specialist in your area — would [Day] morning or
afternoon work better for a quick 15-minute visit? They'll show you
exactly what your savings would look like, no obligation."
  → [book_appointment] with date/time
  → "Perfect! I've booked [Rep Name] for [Day] at [Time]. You'll get
     a confirmation text shortly. Thanks [Name], have a great day!"

CLOSING:
"Thanks for your time, [Name]! Have a wonderful day."
```

### SMS Follow-Up Sequence

```
SMS 1 (Immediately after call, if appointment booked):
"Hi [Name]! This is [Company] Solar confirming your appointment on [Date]
at [Time] with [Rep]. Reply STOP to opt out."

SMS 2 (Day before appointment):
"Reminder: Your solar consultation is tomorrow at [Time]. [Rep] will
visit [Address]. Questions? Reply here. Reply STOP to opt out."

SMS 3 (If no answer on call — Day 0):
"Hi [Name], Sarah from [Company] Solar tried reaching you about saving
on your electric bill. Want to learn how? Reply YES or call us at [#].
Reply STOP to opt out."

SMS 4 (If no answer — Day 3):
"[Name], homes in [Neighborhood] are going solar and saving $100+/mo.
Curious? Reply YES for a free savings estimate. Reply STOP to opt out."

SMS 5 (If no answer — Day 7):
"Last note from [Company] Solar! We won't bug you again. If you ever
want a free solar estimate, text us anytime. Reply STOP to opt out."
```

### Email Nurture Sequence

```
EMAIL 1 (Day 1 — After call or if email-only):
Subject: "Your home at [Address] — solar savings estimate"
Body: Personalized savings estimate based on property data. CTA: book consult.

EMAIL 2 (Day 5):
Subject: "How [Neighbor Count] homes in [ZIP] are cutting electric bills"
Body: Social proof, local installations map, testimonial. CTA: book consult.

EMAIL 3 (Day 14):
Subject: "Maryland solar incentives expiring — what you need to know"
Body: MD tax credit info, federal ITC, urgency. CTA: book consult.

EMAIL 4 (Day 30):
Subject: "Your free solar estimate is still waiting"
Body: Quick re-engagement, simplified CTA. One-click book.

EMAIL 5 (Day 60 — Final):
Subject: "We'll stop emailing (unless you want us to)"
Body: Sunset email, unsubscribe reinforced, one last CTA.
```

### Agent Tool Calls

```python
# Tools available to the AI agent during calls:
tools = [
    {
        "name": "lookup_property",
        "description": "Fetch property details for the current lead",
        "parameters": {"lead_id": "int"}
    },
    {
        "name": "update_lead_status",
        "description": "Update lead status after qualification",
        "parameters": {"lead_id": "int", "status": "str", "reason": "str"}
    },
    {
        "name": "book_appointment",
        "description": "Book appointment with a closer rep",
        "parameters": {"lead_id": "int", "rep_id": "int", "datetime": "ISO8601", "notes": "str"}
    },
    {
        "name": "log_consent",
        "description": "Log consent action (opt-in or opt-out)",
        "parameters": {"lead_id": "int", "consent_type": "str", "channel": "str", "status": "str"}
    },
    {
        "name": "send_sms",
        "description": "Send an SMS to the prospect",
        "parameters": {"lead_id": "int", "template_id": "str", "personalization": "dict"}
    },
    {
        "name": "schedule_callback",
        "description": "Schedule a callback at a specific time",
        "parameters": {"lead_id": "int", "datetime": "ISO8601"}
    },
    {
        "name": "add_note",
        "description": "Add a note to the lead record",
        "parameters": {"lead_id": "int", "content": "str"}
    },
    {
        "name": "end_call",
        "description": "Gracefully end the current call",
        "parameters": {"lead_id": "int", "disposition": "str"}
    }
]
```

### Call Dispositions → CRM Updates

| Disposition | Lead Status | Next Action |
|-------------|-------------|-------------|
| `appointment_booked` | `qualified` | Assign rep, send confirmation SMS |
| `callback_scheduled` | `contacted` | Re-queue for scheduled time |
| `interested_not_ready` | `nurturing` | Enter SMS+email sequence |
| `not_interested` | `closed_lost` | Mark DNC for 90 days, stop outreach |
| `not_homeowner` | `disqualified` | Remove from pipeline |
| `wrong_number` | `bad_data` | Flag for data cleanup |
| `voicemail` | `no_answer` | Queue SMS follow-up |
| `no_answer` | `no_answer` | Retry per schedule |
| `do_not_call` | `dnc` | Immediate DNC, log consent |

---

## F) OUTREACH ORCHESTRATION

### Scheduling Rules

**Time Windows (Maryland):**
- Calls: Mon–Fri 9:00 AM – 8:00 PM ET, Sat 10:00 AM – 5:00 PM ET, No Sunday
- SMS: Mon–Sat 9:00 AM – 9:00 PM ET, No Sunday
- Email: Any time (queue for 8 AM ET delivery)

**Retry Logic:**
- Call: Max 3 attempts, spaced 2 days apart
- SMS: Max 3 messages (Day 0, Day 3, Day 7)
- Email: Max 5 emails over 60 days

**Escalation Path:**
```
Call Attempt 1 (no answer) → wait 4hrs → Call Attempt 2
Call Attempt 2 (no answer) → SMS #1 (next day)
SMS #1 (no reply, 48hrs) → Call Attempt 3
Call Attempt 3 (no answer) → SMS #2 (Day 3) → SMS #3 (Day 7)
Still no engagement → Email nurture sequence (5 emails over 60 days)
After email sequence → Archive lead, re-score in 90 days
```

**Stop Conditions:**
- Prospect says "stop" / "don't call" / "remove" on any channel
- DNC list match detected
- Consent revoked
- Max attempts exhausted on all channels
- Lead marked disqualified/closed

### Lead Lifecycle State Machine

```
                              ┌─────────────┐
                              │   INGESTED   │
                              └──────┬───────┘
                                     │ score computed
                                     ▼
                    ┌────────────────────────────────┐
                    │            SCORED               │
                    └───┬──────────┬─────────────┬───┘
                        │          │             │
                   score≥75    50≤score<75    score<50
                        │          │             │
                        ▼          ▼             ▼
                    ┌───────┐  ┌───────┐   ┌─────────┐
                    │  HOT  │  │ WARM  │   │  COOL   │
                    └───┬───┘  └───┬───┘   └────┬────┘
                        │          │             │
                   call queue   call queue   email only
                        │          │             │
                        ▼          ▼             ▼
                    ┌──────────────────────────────┐
                    │        CONTACTING            │
                    └──┬───────┬──────────┬────────┘
                       │       │          │
                  answered  voicemail  no answer
                       │       │          │
                       ▼       ▼          ▼
               ┌───────────┐  ┌──────────────────┐
               │ CONTACTED │  │   RETRYING        │
               └─────┬─────┘  └────────┬─────────┘
                     │                 │ max retries
            ┌────────┼────────┐        ▼
            │        │        │   ┌──────────┐
            ▼        ▼        ▼   │ NURTURING│ (SMS/Email sequence)
     ┌──────────┐ ┌─────┐ ┌────┐ └────┬─────┘
     │QUALIFIED │ │LOST │ │DNC │      │
     └────┬─────┘ └─────┘ └────┘      │ no engagement
          │                            ▼
          ▼                      ┌──────────┐
     ┌──────────┐                │ ARCHIVED │ (re-score in 90d)
     │ APPT SET │                └──────────┘
     └────┬─────┘
          │
     ┌────┼─────────┐
     │    │          │
     ▼    ▼          ▼
  ┌────┐┌──────┐┌────────┐
  │WON ││LOST  ││NO-SHOW │ → re-queue
  └────┘└──────┘└────────┘
```

---

## G) FRONTEND + CRM UX (MVP)

### Page List & Wireframe Descriptions

#### 1. Dashboard (`/dashboard`)
```
┌─────────────────────────────────────────────────────┐
│  SOLARCOMMAND DASHBOARD              [User ▼] [⚙]  │
├──────────┬──────────┬──────────┬───────────────────│
│ Leads    │ Calls    │ Appts    │ Conversions       │
│ Today    │ Today    │ This Wk  │ This Month        │
│  147     │   89     │   12     │   3 ($45K)        │
├──────────┴──────────┴──────────┴───────────────────│
│                                                     │
│  [Outreach Funnel Chart]     [Score Distribution]   │
│   Scored: 2,340               Hot: 234              │
│   Contacted: 890              Warm: 567             │
│   Qualified: 156              Cool: 1,539           │
│   Appt Set: 45                                      │
│   Won: 12                                           │
│                                                     │
│  [Today's Queue]              [Recent Activity]     │
│   Next 10 calls...            Call log feed...      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

#### 2. Lead List (`/leads`)
```
┌─────────────────────────────────────────────────────┐
│  LEADS  [+ Import] [Export CSV]                      │
├─────────────────────────────────────────────────────│
│ Filters: [County ▼] [Score ▼] [Status ▼] [Search]  │
├─────────────────────────────────────────────────────│
│ Score│ Name          │ Address        │ Status │ Rep │
│  92  │ John Smith    │ 123 Oak St     │ Hot    │ --  │
│  87  │ Jane Doe      │ 456 Elm Ave    │ Appt   │ Bob │
│  73  │ Mike Johnson  │ 789 Pine Rd    │ Warm   │ --  │
│  ...                                                 │
├─────────────────────────────────────────────────────│
│ Showing 1-50 of 2,340  [< 1 2 3 ... 47 >]          │
└─────────────────────────────────────────────────────┘
```

#### 3. Lead Detail (`/leads/:id`)
```
┌─────────────────────────────────────────────────────┐
│  ← Back   JOHN SMITH — 123 Oak St, Annapolis 21401  │
├───────────────────────┬─────────────────────────────│
│  PROPERTY INFO        │  LEAD INFO                   │
│  Built: 2005          │  Score: 92 (Hot)             │
│  Sqft: 2,400          │  Status: Contacted           │
│  Roof: Asphalt shingle│  Assigned: Bob (Closer)      │
│  Value: $425,000      │  Source: SDAT Import         │
│  Utility: BGE         │                              │
│  Est. Bill: $220/mo   │  [Book Appt] [Add Note]      │
├───────────────────────┴─────────────────────────────│
│  TIMELINE                                            │
│  Feb 5 14:32  AI Call — Answered, Interested  [▶]   │
│  Feb 5 14:33  SMS — Confirmation sent                │
│  Feb 4 09:15  Scored: 92                             │
│  Feb 3 22:00  Ingested from SDAT batch               │
├─────────────────────────────────────────────────────│
│  CONSENT LOG                                         │
│  Feb 5  Verbal opt-in to call (recorded)             │
│  Feb 5  SMS opt-in (replied YES)                     │
├─────────────────────────────────────────────────────│
│  NOTES                                               │
│  Feb 5 — "Wife interested, husband skeptical" — AI   │
└─────────────────────────────────────────────────────┘
```

#### 4. Appointment Calendar (`/appointments`)
```
┌─────────────────────────────────────────────────────┐
│  APPOINTMENTS  [+ Manual] [Week ▼]                   │
├─────────────────────────────────────────────────────│
│       Mon 2/10  │  Tue 2/11  │  Wed 2/12  │ ...     │
│  9AM            │            │  Smith     │          │
│  10AM  Jones    │  Brown     │            │          │
│  11AM           │            │  Garcia    │          │
│  12PM           │  Patel     │            │          │
│  ...                                                 │
└─────────────────────────────────────────────────────┘
```

#### 5. Script Management (`/admin/scripts`)
```
┌─────────────────────────────────────────────────────┐
│  CALL SCRIPTS  [+ New Version]                       │
├─────────────────────────────────────────────────────│
│ Version │ Created    │ Status  │ Author │ Actions    │
│ v1.3    │ 2025-02-05 │ Active  │ Admin  │ [View]     │
│ v1.2    │ 2025-01-20 │ Retired │ Admin  │ [View]     │
│ v1.1    │ 2025-01-10 │ Retired │ Admin  │ [View]     │
├─────────────────────────────────────────────────────│
│  [Script Editor — Rich Text with Variable Tags]      │
│  {{name}}, {{address}}, {{county}}, {{company}}      │
└─────────────────────────────────────────────────────┘
```

#### 6. Compliance/Audit Panel (`/admin/compliance`)
```
┌─────────────────────────────────────────────────────┐
│  COMPLIANCE & AUDIT                                  │
├──────────┬──────────────────────────────────────────│
│ DNC List │ Consent Log │ Audit Log │ Call Recordings │
├──────────┴──────────────────────────────────────────│
│  Filters: [Date Range] [Type ▼] [User ▼]           │
│                                                      │
│  Timestamp       │ Actor  │ Action  │ Detail         │
│  Feb 5 14:32:01  │ System │ Call    │ Lead #4521     │
│  Feb 5 14:32:45  │ AI     │ Consent │ Verbal opt-in  │
│  Feb 5 14:33:02  │ System │ SMS     │ Confirmation   │
│  ...                                                 │
├─────────────────────────────────────────────────────│
│  [Export Audit Log]  [DNC Upload]  [Consent Report]  │
└─────────────────────────────────────────────────────┘
```

### Role-Based Access Control

| Page / Action | Admin | Rep (Closer) | Ops |
|---------------|-------|-------------|-----|
| Dashboard | Full | Own metrics | Full |
| Lead List | Full | Assigned only | Full |
| Lead Detail | Full | Assigned only | Read-only |
| Book Appointment | Yes | Yes (own) | Yes |
| Script Management | Full CRUD | Read only | Read only |
| Compliance Panel | Full | No access | Read-only |
| User Management | Full | No access | No access |
| Data Import | Full | No access | Yes |
| DNC Management | Full | No access | Yes |

---

## H) TECH STACK + REPO PLAN

### Recommended Stack

| Layer | Choice | Justification |
|-------|--------|---------------|
| **Backend** | FastAPI (Python) | Fastest Python API framework; native async; Pydantic models = schema validation; rich ecosystem for ML/data (v2 scoring); team likely has Python experience from data work |
| **Frontend** | Next.js 14 (App Router) | SSR for dashboard perf; React ecosystem; great DX; easy deployment |
| **Database** | PostgreSQL 16 | ACID, JSON support for flexible fields, PostGIS for geo queries, battle-tested |
| **Queue** | Redis + Celery | Python-native, well-documented, handles scheduling/retry; BullMQ would need Node workers |
| **Voice/SMS** | Twilio | Industry standard, MD numbers, call recording, programmable voice |
| **Email** | SendGrid | Reliable, templates, analytics, good free tier |
| **LLM** | OpenAI GPT-4o-mini | Fast, cheap, function-calling support for agent tools |
| **Hosting (MVP)** | Render | Simple deploys, managed Postgres, free Redis, auto-TLS, affordable ($50-100/mo MVP) |
| **Monitoring** | Sentry + Render logs | Error tracking + request logging, free tiers |

### Monorepo Structure

```
SolarCommand/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
├── docs/
│   └── SYSTEM_DESIGN.md          ← This document
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               ← FastAPI app
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py         ← Settings (env vars)
│   │   │   ├── database.py       ← DB connection
│   │   │   └── security.py       ← Auth helpers
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schema.py         ← SQLAlchemy models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── leads.py          ← Lead endpoints
│   │   │   ├── outreach.py       ← Outreach endpoints
│   │   │   ├── appointments.py   ← Appointment endpoints
│   │   │   └── admin.py          ← Admin endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── scoring.py        ← Scoring engine
│   │   │   ├── orchestrator.py   ← Outreach scheduling
│   │   │   └── ai_agent.py       ← LLM agent logic
│   │   └── workers/
│   │       ├── __init__.py
│   │       ├── celery_app.py     ← Celery config
│   │       └── tasks.py          ← Background tasks
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_leads.py
│       ├── test_scoring.py
│       └── test_outreach.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx          ← Dashboard
│       │   ├── leads/
│       │   ├── appointments/
│       │   └── admin/
│       └── components/
│
└── infrastructure/
    ├── render.yaml               ← Render blueprint
    └── init.sql                  ← Bootstrap SQL
```

---

## I) IMPLEMENTATION ROADMAP

### 30/60/90-Day Plan

#### Days 1–30: Foundation
- [x] System design (this document)
- [ ] Repo setup, CI/CD, Docker Compose
- [ ] Database schema + Alembic migrations
- [ ] FastAPI skeleton with all model classes
- [ ] Lead ingest endpoint (bulk JSON + single)
- [ ] Scoring engine v1 (heuristic)
- [ ] Score endpoint
- [ ] Basic Celery worker + Redis
- [ ] Outreach enqueue endpoint
- [ ] Unit tests for scoring + ingest
- **Milestone**: Can ingest properties, score them, and queue outreach jobs.

#### Days 31–60: Outreach + CRM
- [ ] Twilio integration (voice + SMS)
- [ ] AI voice agent v1 (script-following, basic qualification)
- [ ] SMS sequence automation
- [ ] SendGrid email integration
- [ ] Outreach orchestrator (scheduling, retry, escalation)
- [ ] Consent logging on every touch
- [ ] Next.js frontend: Dashboard + Lead List + Lead Detail
- [ ] Appointment booking flow
- [ ] Basic auth (API keys → JWT)
- **Milestone**: End-to-end flow: ingest → score → call → qualify → book appointment.

#### Days 61–90: Polish + Launch
- [ ] Rep View: calendar, assigned leads, notes
- [ ] Admin panel: scripts, compliance, audit log
- [ ] RBAC (Admin/Rep/Ops)
- [ ] DNC list import + scrubbing
- [ ] Call recording storage + playback
- [ ] Dashboard KPIs + charts
- [ ] Load test with 5K leads in Anne Arundel County
- [ ] Security audit (OWASP top 10)
- [ ] Deploy to Render (staging → production)
- [ ] Onboard 2 closers, run pilot
- **Milestone**: Production MVP live with real leads in Anne Arundel + Howard County.

### MVP Backlog (User Stories)

| # | Story | Acceptance Criteria |
|---|-------|-------------------|
| 1 | As admin, I can bulk-import property records | Upload JSON/CSV → records appear in DB, deduped |
| 2 | As system, I score all new leads automatically | Score computed within 5 min of ingest, stored in lead_score |
| 3 | As system, I queue hot leads for immediate call | Leads ≥75 score queued within 10 min |
| 4 | As AI agent, I call and qualify a prospect | Call placed via Twilio, transcript logged, disposition recorded |
| 5 | As AI agent, I book an appointment for qualified leads | Appointment created, rep notified, confirmation SMS sent |
| 6 | As AI agent, I send SMS follow-ups to no-answers | SMS sent per sequence rules, opt-out honored instantly |
| 7 | As rep, I see my assigned leads and appointments | Rep View shows filtered list + calendar |
| 8 | As rep, I can add notes to a lead | Notes saved with timestamp + author |
| 9 | As admin, I can view all consent records | Consent log filterable by date, lead, type |
| 10 | As admin, I can manage call scripts with versioning | Create, edit, activate/retire script versions |
| 11 | As system, I never call a DNC number | DNC scrub runs before every outreach attempt |
| 12 | As system, I log every action to audit trail | All mutations have audit_log entry |

### Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|------------|-------|
| 1 | TCPA complaint | Medium | High | Consent-first, DNC scrub, audit logs, legal review | Ops |
| 2 | Twilio account suspended | Low | High | Follow Twilio acceptable use, warm up numbers gradually | Dev |
| 3 | Low answer rates | High | Medium | Multi-channel, optimal timing, local caller ID | Dev/Ops |
| 4 | AI says something wrong | Medium | Medium | Strict guardrails, call recording review, script versioning | Dev |
| 5 | Data vendor discontinues | Low | Medium | Abstract data source interface, 2+ vendor contracts | Data Eng |
| 6 | Scaling bottleneck at 10K leads | Low | Low | Postgres indexing plan, Celery horizontal scaling | Dev |
| 7 | MD regulation change | Low | Medium | Monitor MD PSC, configurable compliance rules per state | Ops |

---

## K) COMPLIANCE NOTES (NON-LEGAL ADVICE)

*Disclaimer: This is a technical compliance checklist, not legal advice. Consult a TCPA attorney before production launch.*

### TCPA / Consent Compliance Checklist

1. **Prior Express Written Consent** for autodialed/prerecorded calls to cell phones.
   - Implementation: Do NOT autodial without consent. For cold outreach, use live-transfer or 1:1 dialing.
   - Alternative: Use "click-to-call" where a human initiates, AI takes over after connect.

2. **Caller ID**: Always display a valid, callable number.
   - Implementation: Twilio local MD number, inbound capable.

3. **Time Restrictions**: No calls before 8 AM or after 9 PM (recipient's local time).
   - Implementation: Enforce in Outreach Orchestrator scheduling rules. Maryland is Eastern Time.

4. **DNC Compliance**:
   - Scrub against National DNC Registry (subscribe to FTC DNC data).
   - Maintain internal DNC list (prospects who opt out).
   - Scrub before EVERY outreach attempt.
   - Implementation: `dnc_check()` gate in orchestrator, logs result.

5. **Opt-Out Handling**:
   - Voice: Honor "stop" / "remove" / "don't call" immediately.
   - SMS: Honor "STOP" keyword instantly (Twilio handles automatically).
   - Email: Unsubscribe link in every email (CAN-SPAM).
   - Implementation: Update `consent_log` with `opted_out`, trigger in all channels.

6. **Record Keeping**:
   - Store consent evidence (timestamp, channel, recording/transcript).
   - Store opt-out evidence.
   - Retain for minimum 5 years.
   - Implementation: `consent_log` table with immutable inserts, S3 call recordings.

7. **Maryland-Specific**:
   - MD is a one-party consent state for call recording (only one party needs to consent).
   - However, best practice: disclose recording at call start.
   - MD Home Solicitation Sales Act: 3-day cancellation right for door-to-door sales.
   - Implementation: Include disclosure in opening script.

8. **Script Version Control**:
   - Every call uses a versioned script.
   - Script changes create new versions (old versions never deleted).
   - Audit trail shows which script version was used for each call.
   - Implementation: `script_version` table, `outreach_attempt.script_version_id` FK.

9. **Audit Trail**:
   - Every lead status change, outreach attempt, consent change, and admin action logged.
   - Logs are append-only (no updates/deletes).
   - Implementation: `audit_log` table with `actor`, `action`, `entity`, `old_value`, `new_value`, `timestamp`.

### Safe Calling Patterns

```
BEFORE EACH CALL:
  1. Check internal DNC list         → block if match
  2. Check national DNC registry     → block if match
  3. Check consent_log for opt-outs  → block if match
  4. Check time window               → defer if outside hours
  5. Check max attempt count         → stop if exceeded
  6. Check lead status               → skip if closed/disqualified
  7. Log pre-call check to audit     → proceed only if all pass

DURING CALL:
  8. Identify company + purpose in first 10 seconds
  9. Disclose recording
  10. Offer opt-out at any time

AFTER CALL:
  11. Log disposition + transcript
  12. Log any consent changes
  13. Update lead status
  14. Schedule next action or stop
```
