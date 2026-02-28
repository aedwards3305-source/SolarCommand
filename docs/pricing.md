# SolarCommand Pricing Model

## Tiered Pricing

### Starter — $497/month
**For:** Small solar companies (1-3 reps, up to 1,000 leads)

| Feature | Included |
|---------|----------|
| Lead ingestion + scoring | Up to 1,000 leads/month |
| AI-powered SMS outreach | 500 AI classifications/month |
| Next Best Action (NBA) | Daily batch |
| QA compliance reviews | Automated |
| Rep briefs | On-demand |
| Dashboard + reporting | Full access |
| Voice integration | Not included |
| Contact enrichment | Not included |
| Users | Up to 3 |

---

### Growth — $1,297/month
**For:** Growing solar companies (3-10 reps, up to 5,000 leads)

| Feature | Included |
|---------|----------|
| Lead ingestion + scoring | Up to 5,000 leads/month |
| AI-powered SMS outreach | 2,500 AI classifications/month |
| Next Best Action (NBA) | Real-time + nightly batch |
| QA compliance reviews | Automated + weekly insights |
| Rep briefs | On-demand |
| Dashboard + reporting | Full access |
| Voice integration (Twilio) | 500 minutes/month |
| Contact enrichment (PDL) | 1,000 lookups/month |
| Contact validation (Melissa) | 2,500 validations/month |
| Script A/B testing | Included |
| AI memory / learning loop | Included |
| Users | Up to 10 |

---

### Enterprise — Custom Pricing
**For:** Multi-location solar companies (10+ reps, unlimited leads)

| Feature | Included |
|---------|----------|
| Lead ingestion + scoring | Unlimited |
| AI-powered SMS + email outreach | Unlimited AI classifications |
| Next Best Action (NBA) | Real-time |
| QA compliance reviews | Automated + custom rules |
| Rep briefs | On-demand |
| Dashboard + reporting | Full access + custom reports |
| Voice integration (Twilio/Vapi) | Unlimited minutes |
| AI-driven voice (Vapi) | Conversational AI calls |
| Contact enrichment (PDL) | Unlimited lookups |
| Contact validation (Melissa) | Unlimited |
| Script A/B testing | Included |
| AI memory / learning loop | Per-rep, per-county insights |
| Custom integrations | CRM, calendar, telephony |
| Dedicated support | Slack channel + onboarding |
| Users | Unlimited |
| SLA | 99.9% uptime |

---

## Variable Cost Components

These costs are passed through at cost plus a margin:

| Component | Provider | Cost Basis | Our Margin |
|-----------|----------|------------|------------|
| AI (Claude) | Anthropic | ~$0.003/call classification | Included in tier |
| Voice calls | Twilio | $0.014/min outbound | 20% markup |
| Voice calls | Vapi | $0.05/min AI-driven | 15% markup |
| SMS | Twilio | $0.0079/segment | 20% markup |
| Enrichment | PDL | $0.10/lookup | Included in tier |
| Validation | Melissa | $0.02/record | Included in tier |

---

## Cost Tracking

SolarCommand tracks every AI API call with:
- Token count (input + output)
- Cost in USD (per-model rates)
- Latency in milliseconds

Admins can view real-time cost dashboards at `/admin/ai-runs` showing:
- Daily spend by task type
- Error rates
- Average latency
- Per-lead AI cost

---

## ROI Model

### Assumptions (Growth Tier)
- Average solar installation: $25,000
- Close rate without SolarCommand: 8%
- Close rate with SolarCommand: 12% (+50% improvement)
- Leads per month: 3,000
- Reps: 5

### Monthly Impact
| Metric | Without | With SolarCommand | Delta |
|--------|---------|-------------------|-------|
| Appointments set | 120 | 180 | +60 |
| Deals closed | 24 | 36 | +12 |
| Revenue | $600,000 | $900,000 | +$300,000 |
| SolarCommand cost | — | $1,297 | — |
| **ROI** | — | — | **231x** |

---

## Implementation Timeline

| Week | Milestone |
|------|-----------|
| 1 | Account setup, data migration, team onboarding |
| 2 | Lead ingestion, scoring calibration, first outreach |
| 3 | Voice integration, enrichment pipeline active |
| 4 | Full AI Operator running, weekly insights, A/B tests |
