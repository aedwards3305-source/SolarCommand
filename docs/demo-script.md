# SolarCommand — 6-Minute Live Demo Script

**Format:** Presenter-led walkthrough with live product. Each section includes what to show on screen, what to say, and compliance proof points to call out.

**Setup:** Browser open with SolarCommand at `http://localhost:3000`, logged in as admin. Have a sample CSV file ready. Dashboard should show existing data so it doesn't look empty.

---

## Minute 0:00–0:45 — Dashboard & Context Setting

**Screen:** Dashboard page (`/dashboard`)

**Say:**

> "This is SolarCommand. What you're looking at is the operations dashboard — the view your sales manager sees every morning.

> Up top: your KPIs. Total leads in the system, how many scored as Hot, Warm, and Cool, appointments scheduled, and total outreach attempts. These update in real time.

> Below that: average lead score across the pipeline and your conversion rate. And this grid breaks down every lead by status — from ingested through closed-won. You can see exactly where your pipeline stands.

> Down here is something different. This is your AI Insights panel. Every Monday, the AI operator reviews your prior week's performance and writes a narrative summary — key drivers, recommendations, counties to focus on. This isn't a chart. It's an actual briefing. And it's generated from your data, not a template."

**Compliance proof point:**
> "Notice: the insights cite specific metrics from your pipeline. If you drill into the admin panel, you can see the exact AI call that generated this — the prompt, the output, the token count, and the cost. Full transparency."

---

## Minute 0:45–1:30 — CSV Upload & Lead Ingestion

**Screen:** Navigate to Upload page (`/upload`)

**Say:**

> "Let's start from the beginning. Your leads come in as a CSV — exported from your lead provider, your county records, wherever you source them.

> [Select CSV file] This file has about 50 properties. Standard fields: address, county, owner name, phone, email, property type, year built, roof area, assessed value, utility zone, tree cover percentage, and whether there's existing solar.

> [Click Upload] The system ingests each row, creates a property record and a lead record, and tells us the results: 48 ingested, 2 skipped — those had duplicate addresses already in the system. No errors.

> Every lead starts in 'ingested' status. Nothing happens to them until we score them."

**Compliance proof point:**
> "The audit log already has 48 entries — one per lead ingested, timestamped, with the actor recorded. Nothing enters this system without a paper trail."

---

## Minute 1:30–2:30 — Lead Scoring & Detail View

**Screen:** Navigate to Leads page (`/leads`), click into a Hot lead

**Say:**

> "Here's our lead list. I'll filter to show the ones we just uploaded. Let me click into this one — a single-family home in Baltimore County.

> [Click lead name, land on detail page]

> This is the lead detail view — the command center for this lead. Let's start with the score.

> [Click 'Score Lead' button if not yet scored, or point to existing score]

> This lead scored 82 out of 100 — that's Hot. But the number alone isn't the point. Look at the breakdown: 10 scoring factors, each with a progress bar showing how many points it earned out of its maximum.

> Roof Age: 13 out of 15 — the roof is 22 years old, prime for replacement with solar panels. Ownership: 15 out of 15 — owner-occupied. Roof Area: 12 out of 15 — 1,800 square feet, plenty of space. Utility Rate: 10 out of 10 — BGE zone, highest rates in the state. Shade: 8 out of 10 — only 15% tree cover. Neighborhood: 7 out of 10 — 30% of neighbors already have solar.

> Your rep doesn't need to guess. They can see *why* this lead is worth their time. And if a lead scores 35, they can see *why* it isn't — maybe it's a renter, or it already has panels."

**Compliance proof point:**
> "The scoring algorithm is deterministic — same inputs, same score, every time. There's no AI in the scoring. It's a weighted formula. That means it's explainable, auditable, and defensible if anyone asks why a lead was prioritized."

---

## Minute 2:30–3:30 — Enrichment & Contact Intelligence

**Screen:** Stay on lead detail, scroll to Contact Intelligence card

**Say:**

> "Before our rep calls, let's make sure we have good contact data.

> [Click 'Enrich' button]

> This triggers two things in the background. First, People Data Labs searches for this person and returns additional contact information — we found a second email and a work phone. It also pulled their job title and LinkedIn URL. Second, Melissa Data validates what we already had: the primary phone is a mobile — that's important for TCPA — the carrier is Verizon, the email is deliverable.

> [Point to validation badges]

> Green badges: phone valid, mobile type, email deliverable. Your rep is calling a real number that's actually a cell phone. That matters for compliance, and it matters for connect rate.

> The confidence score here is 0.78 — above our 0.5 threshold. If PDL returns low-confidence data, we flag it rather than auto-populating bad information."

**Compliance proof point:**
> "Phone type detection is critical for TCPA. Calling a landline is different from calling a mobile under the law. We surface that data *before* the call, not after a complaint."

---

## Minute 3:30–4:30 — Outreach, Voice Call & AI Processing

**Screen:** Stay on lead detail

**Say:**

> "Now let's reach out. I'll hit 'Queue Outreach.'

> [Click Queue Outreach]

> The orchestrator just ran through its compliance checklist: Is this lead on the DNC list? No. Have we hit the attempt limit? No — first contact. Is it within calling hours? Yes — it's 2pm Eastern on a Tuesday. Is there consent? Yes — implied consent from the lead source, logged in the consent history here.

> The system selected voice as the channel — it's the highest-priority channel during business hours. If it were 9pm, it would have fallen back to SMS. If it were Sunday, it would have queued for Monday morning.

> [Click 'Voice Call' button]

> The call is now being placed via Twilio. In the background, the system created an outreach attempt record and a conversation transcript record. Let me scroll down to the recordings section.

> [Wait a moment, then point to Voice Recordings card]

> When the call completes, three AI tasks fire automatically: the transcript gets summarized with sentiment analysis, a 9-point compliance QA review runs, and objections are extracted. Let me show you that QA review."

**Compliance proof point:**
> "The outreach orchestrator enforces rules that don't depend on rep behavior. Quiet hours aren't a guideline — they're a gate. The system physically will not place a call outside the configured window. And the post-call QA isn't optional — it runs on every conversation, automatically."

---

## Minute 4:30–5:15 — Compliance QA, NBA & Rep Brief

**Screen:** Navigate briefly to Lead QA tab, then back to detail page

**Say:**

> "Here's the QA review for this call. Score: 87 out of 100 — passing. The 9-point checklist: agent identified themselves — pass. Recording disclosure — pass. 'Is now a good time?' — pass. No false savings claims — pass. Respected opt-out — pass.

> One flag, severity 'info': the agent could have been clearer on the monitoring disclosure. That's not a violation, but it's coaching feedback that surfaces automatically.

> [Navigate back to lead detail, point to NBA card]

> Now look at the Next Best Action. The AI has analyzed the conversation, the score, the enrichment data, and the outreach history, and it's recommending: 'Send follow-up SMS tomorrow at 10am with a savings estimate.' Confidence: 84%. Reason codes: 'expressed interest,' 'requested more information,' 'optimal SMS window.'

> [Point to AI Brief card]

> And here's the rep brief. A two-sentence summary of the lead, a three-point talk track tailored to this property, objection handlers for the two most likely pushbacks — 'too expensive' and 'roof condition' — and a recommended approach. Your rep reads this in 30 seconds before their next touchpoint. They're not improvising."

**Compliance proof point:**
> "The NBA respects hard rules first — it will never recommend contacting a DNC lead or calling outside quiet hours, regardless of what the AI model thinks. Deterministic rules override AI reasoning. And the QA review creates a compliance record that exists whether or not anyone looks at it. If a regulator asks about this call in two years, the record is there."

---

## Minute 5:15–5:45 — Admin: AI Observability & Cost Tracking

**Screen:** Navigate to Admin > AI Runs (`/admin/ai-runs`)

**Say:**

> "Last thing — and this is what your ops team and compliance team will care about most.

> This is the AI Runs dashboard. Every single AI call the system made today — SMS classifications, QA reviews, objection extractions, NBA decisions, rep briefs, script suggestions. For each one: the task type, the model used, which lead it was for, latency, token count, cost in dollars, and pass/fail status.

> [Expand one row]

> I can drill into any run and see the full input prompt and the full output. The exact text that was sent to Claude, and the exact response that came back. Temperature, prompt version, token breakdown — input and output separately.

> Today's stats: 47 runs, 0 errors, average latency 1.2 seconds, total cost: $0.14. That's fourteen cents for a full day of AI-powered outreach intelligence.

> [Point to cost stat]

> No black boxes. No invoice surprises. Every dollar accounted for."

---

## Minute 5:45–6:00 — Close

**Screen:** Back to Dashboard

**Say:**

> "So that's SolarCommand end to end. A lead enters as a row in a CSV. It gets scored on 10 solar-specific factors. Contact data is enriched and validated. Outreach is orchestrated across voice, SMS, and email with compliance enforced at every step. After every conversation, the AI operator summarizes, QA-reviews, extracts objections, and recommends the next action. Every AI decision is logged, auditable, and costs pennies.

> Your reps spend less time guessing and more time closing. Your compliance team sleeps at night. And your cost is predictable down to the token.

> Let's talk about running this with your data."

---

## Demo Prep Checklist

- [ ] Docker services running (`docker compose up -d`)
- [ ] Seed data loaded (20+ leads with scores, some with outreach history)
- [ ] Anthropic API key configured in `.env`
- [ ] Sample CSV ready with 40-50 properties
- [ ] At least one completed voice call with QA review in the system
- [ ] At least one SMS thread with AI classification
- [ ] AI Runs table populated (run a few NBA and brief generations beforehand)
- [ ] Admin account: `admin@solarcommand.local` / `SolarAdmin1!`
- [ ] Browser at `http://localhost:3000`, logged in, dashboard loaded

## Handling Questions

**"Can the AI make calls autonomously?"**
> "The AI can drive the conversation via Vapi on the Enterprise tier — that's a full conversational AI agent. But by default, the system is suggest-only. It recommends who to call, when, and what to say. A human makes the call. You can turn on auto-actions when your team is ready, but we ship with guardrails on."

**"What happens if the AI goes down?"**
> "The system falls back to deterministic defaults. Leads still score, outreach still respects compliance rules, and the queue still processes. AI adds intelligence — it doesn't block the workflow."

**"How is this different from [competitor]?"**
> "Most AI outreach tools are general-purpose — they generate text but don't understand solar signals. We score on roof age, utility zone, shade, and neighborhood adoption. And the biggest difference: every AI decision we make is logged with full input/output. If your compliance team asks 'why did the system recommend this?' — we can show them in 60 seconds."

**"What does this cost on a per-lead basis?"**
> "AI classification runs about $0.003 per call. Voice is Twilio rates plus a small margin. Enrichment is $0.10 per lookup. On the Growth tier, most teams land at $1,500-1,800 per month all-in for 3,000-5,000 leads. One extra closed deal covers the platform for a year and a half."
