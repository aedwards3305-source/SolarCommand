# SolarCommand Pitch Deck — 7 Slides

---

## Slide 1: Cover

**Title:** SolarCommand
**Subtitle:** AI-Powered Lead Intelligence for Solar Sales Teams

**Bullets:**
- Score every lead before you dial
- Automate outreach across voice, SMS, and email
- Stay TCPA-compliant by default, not by accident

**Speaker Notes:**
Good morning. If you run a solar sales operation, you know the math: your reps spend half their day chasing leads that were never going to convert. Meanwhile, leads that *would* convert go stale because nobody called them in time. SolarCommand fixes that pipeline. We score every property before a rep touches it, automate multi-channel outreach with built-in compliance, and use AI to tell your team exactly who to call next and what to say. Let me show you what that looks like.

---

## Slide 2: The Problem

**Title:** Solar Sales Teams Are Bleeding Money on Bad Leads

**Bullets:**
- The average solar rep dials 80-120 leads/day — fewer than 15% connect
- No reliable way to rank leads before first contact: reps guess
- Compliance exposure is growing: TCPA lawsuits average $1,500 per violation, per call
- Generic outreach tools don't understand solar-specific signals (roof age, utility zone, shade coverage, neighborhood adoption)
- When a rep *does* connect, they lack context — no talk track, no objection prep

**Speaker Notes:**
Let's level-set on the pain. Solar lead gen is a volume game, but it's an expensive one. Your reps are dialing through lists with no signal about who's actually a good fit. When they do connect, they're improvising. And the compliance landscape is tightening — TCPA class actions are up 30% year-over-year, and a single campaign mistake can cost six figures. The tools most teams use today — dialers, CRMs, generic AI assistants — don't solve the root problem. They make it faster to do the wrong thing.

---

## Slide 3: The Solution

**Title:** SolarCommand: Score, Reach, Convert — With a Compliance Paper Trail

**Bullets:**
- **10-Factor Solar Readiness Score (0-100):** Roof age, area, ownership, home value, utility rate zone, shade, neighborhood adoption, income, property type, existing solar — all weighted and explainable
- **Multi-Channel Outreach Engine:** Voice (Twilio / Vapi AI), SMS, and email — with automatic channel escalation based on time-of-day rules and attempt limits
- **AI Operator (Claude-Powered):**
  - Classifies inbound SMS intent in real time
  - Generates rep briefs with talk tracks and objection handlers
  - Recommends Next Best Action (who to call, when, via which channel)
  - Runs compliance QA on every conversation — 9-point checklist, scored 0-100
- **Contact Enrichment:** People Data Labs + Melissa Data — phone/email validation, job title, LinkedIn, carrier detection
- **Full Audit Trail:** Every action, every AI call, every cost — logged and queryable

**Speaker Notes:**
SolarCommand is a purpose-built lead intelligence platform for solar. Three things happen when a lead enters the system. First, we score it using 10 property-specific factors — not generic demographic data, but roof age, utility zone, shade coverage, neighborhood solar adoption. Second, we orchestrate outreach across voice, SMS, and email with built-in compliance gates — quiet hours, DNC scrubbing, consent tracking, attempt limits. Third, our AI operator runs in the background: classifying inbound messages, generating rep briefs, recommending the next best action, and QA-reviewing every conversation for compliance. Every single action — human or AI — is logged with full audit detail. This isn't a black box. It's a system your compliance team can actually defend.

---

## Slide 4: What Makes This Different

**Title:** Purpose-Built for Solar — Not Another Generic LLM Wrapper

| | Generic LLM Outreach Tools | SolarCommand |
|---|---|---|
| **Lead Scoring** | Demographic guesses or none | 10-factor solar-specific model (roof, utility, shade, etc.) |
| **Compliance** | "Follow the rules" disclaimer | TCPA enforcement built in: quiet hours, DNC, consent logs, opt-out detection, 9-point QA on every call |
| **AI Transparency** | Black-box responses | Every AI call logged: input, output, tokens, cost, latency — fully auditable |
| **Fallback Behavior** | Fails silently or hallucinates | Deterministic fallbacks when AI is unavailable — system never guesses |
| **Auto-Actions** | AI acts autonomously by default | Suggest-only mode by default; human-in-the-loop on every risky decision |
| **Cost Control** | Unlimited API burn | Token-level cost tracking, batch size limits, configurable spend caps |
| **Domain Context** | Generic prompts | Solar-specific prompts, objection libraries, organizational memory that learns per-county and per-rep |

**Speaker Notes:**
You might be thinking: "We've looked at AI outreach tools before." Here's the difference. Most of those tools are thin wrappers around a language model. They generate messages, but they don't understand solar. They don't know that a 25-year-old roof in a BGE utility zone with 40% neighborhood adoption is a fundamentally different lead than a condo with existing panels. SolarCommand scores on those signals. More importantly, most AI tools operate as black boxes. Ours logs every AI call — every input, every output, every token, every cost. Your compliance officer can audit any decision the system made. And by default, the AI suggests — it doesn't act. A human approves every outbound action until you explicitly turn on auto-mode. That's a design choice, not a limitation.

---

## Slide 5: Outcomes

**Title:** What Changes When You Deploy SolarCommand

**Bullets:**

**Higher Connect Rate**
- Reps call the highest-scored leads first, during the optimal window
- AI-recommended Next Best Action improves channel selection
- Contact enrichment fills in missing phones and emails before first dial
- Typical improvement: 15% connect rate → 25%+

**Fewer Wasted Site Visits**
- Pre-qualified leads mean reps visit homes that are actually viable
- Score breakdown flags disqualifiers early (existing solar, renter, heavy shade)
- Typical improvement: 30-40% reduction in no-value appointments

**Controlled, Predictable Cost**
- Every AI call, voice minute, SMS, and enrichment lookup is tracked to the penny
- Batch limits and spend caps prevent runaway costs
- Full cost visibility in the admin dashboard — no invoice surprises

**Compliance Peace of Mind**
- Automated QA catches issues before they become lawsuits
- Consent logs with evidence chains satisfy regulatory audits
- Opt-out processing is deterministic — no AI interpretation of "STOP"

**Speaker Notes:**
Let me talk outcomes, not features. First: connect rate. When your reps start every day with a ranked list — hottest leads first, best channel selected, contact data validated — they connect more often. Our scoring model combined with enrichment and NBA typically moves teams from a 15% connect rate to north of 25%. Second: fewer wasted site visits. The score breakdown tells you *why* a lead scored the way it did. If someone's a renter on a condo with existing panels, you know before anyone gets in a truck. Teams see a 30-40% reduction in no-value appointments. Third: cost. Every dollar this system spends — AI tokens, voice minutes, SMS segments, enrichment lookups — is tracked and visible in the admin console. You set the batch limits. You control the spend. And fourth: compliance. The QA engine reviews every conversation against a 9-point checklist. Opt-out detection is deterministic — it's keyword matching, not AI interpretation. Consent logs carry evidence chains. When regulators ask how you handled a specific lead, you pull the audit log and show them.

---

## Slide 6: Pricing

**Title:** Simple Platform Fee + Transparent Usage

**Bullets:**

**Starter — $497/month**
- Up to 1,000 leads/month, 3 users
- Lead scoring + AI SMS classification (500/month)
- Daily NBA batch
- No voice or enrichment
- Best for: small teams proving out AI-assisted outreach

**Growth — $1,297/month** *(Recommended)*
- Up to 5,000 leads/month, 10 users
- Everything in Starter, plus:
- Voice integration: 500 minutes/month (Twilio)
- Enrichment: 1,000 PDL lookups + 2,500 Melissa validations
- Real-time NBA + script A/B testing + AI memory loop
- Best for: growing teams ready to automate the full pipeline

**Enterprise — Custom**
- Unlimited leads, users, voice (including Vapi conversational AI)
- Custom integrations (CRM, calendar, telephony)
- Dedicated support + SLA
- Best for: multi-location operations

**Usage passed through at cost + margin:**
| Component | Rate |
|---|---|
| AI (Claude) | ~$0.003/classification — included in platform fee |
| Voice (Twilio) | $0.017/min |
| Voice (Vapi AI) | $0.058/min |
| SMS | $0.0095/segment |
| Enrichment (PDL) | $0.10/lookup |
| Validation (Melissa) | $0.02/record |

**Speaker Notes:**
Pricing is straightforward: a platform fee that covers the software, AI classifications, and support — plus transparent pass-through on usage-based services like voice, SMS, and enrichment. We recommend most teams start on Growth. That gives you the full pipeline — scoring, enrichment, voice, SMS, AI operator, A/B testing — for $1,297 a month. Usage costs are passed through with a small margin, and every dollar is visible in your admin dashboard. To put it in perspective: if Growth helps you close just one additional deal per month — on a $25,000 average installation — that's a 19x return on the platform fee alone. Starter is there if you want to prove the scoring and SMS intelligence before adding voice. Enterprise is there when you need unlimited capacity and custom integrations.

---

## Slide 7: Next Steps

**Title:** Get Started in Under a Week

**Bullets:**
- **Day 1:** Connect your lead source (CSV upload or API integration)
- **Day 2:** Configure scoring weights for your market (utility zones, county focus)
- **Day 3:** Connect Twilio for voice + SMS; set compliance rules
- **Day 4:** Load your scripts; AI operator begins learning
- **Day 5:** Reps log in to a ranked, enriched, actionable pipeline

**Call to Action:**
- 30-minute guided demo with your data
- Pilot program: 30 days on Growth tier, cancel anytime
- Contact: [sales@solarcommand.io]

**Speaker Notes:**
Implementation is fast because the system is self-contained. You upload a CSV or connect your lead source, configure your scoring weights for your specific market, connect Twilio, and go. The AI operator starts learning from day one — it watches your conversations, extracts objections, and feeds those patterns back into the prompts. By the end of the first week, your reps have a ranked pipeline with enriched contact data, AI-generated talk tracks, and a compliance system running in the background. We offer a 30-day pilot on the Growth tier with no long-term commitment. Let's schedule 30 minutes to run the demo with your actual data — I think you'll see the difference immediately. Thank you.
