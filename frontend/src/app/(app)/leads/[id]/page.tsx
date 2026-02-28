"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { statusColor, formatDate, formatDateTime, formatCurrency, cn } from "@/lib/utils";

type LeadDetail = Awaited<ReturnType<typeof api.getLeadDetail>>;

interface NBADecision {
  id: number;
  lead_id: number;
  recommended_action: string;
  recommended_channel: string | null;
  schedule_time: string | null;
  reason_codes: string[] | null;
  confidence: number;
  applied: boolean;
  expires_at: string | null;
  created_at: string;
}

interface RepBrief {
  summary: string;
  talk_track: string[];
  objection_handlers: string[];
  recommended_approach: string;
  risk_factors: string[] | null;
}

interface Objection {
  id: number;
  tag: string;
  confidence: number;
  evidence_span: string | null;
  created_at: string;
}

interface Recording {
  id: number;
  call_sid: string | null;
  provider: string | null;
  recording_url: string | null;
  duration_seconds: number | null;
  call_status: string | null;
  ai_summary: string | null;
  ai_sentiment: string | null;
  created_at: string;
}

interface EnrichmentData {
  enrichment: {
    provider: string;
    full_name: string | null;
    emails: Array<{ email: string; type: string }> | null;
    phones: Array<{ number: string; type: string }> | null;
    job_title: string | null;
    linkedin_url: string | null;
    confidence: number;
    updated_at: string;
  } | null;
  validation: {
    provider: string;
    phone_valid: boolean | null;
    phone_type: string | null;
    phone_carrier: string | null;
    email_valid: boolean | null;
    email_deliverable: boolean | null;
    address_valid: boolean | null;
    confidence: number;
    updated_at: string;
  } | null;
}

export default function LeadDetailPage() {
  const params = useParams();
  const leadId = Number(params.id);
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [nba, setNba] = useState<NBADecision | null>(null);
  const [brief, setBrief] = useState<RepBrief | null>(null);
  const [objections, setObjections] = useState<Objection[]>([]);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [enrichment, setEnrichment] = useState<EnrichmentData | null>(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [callingLead, setCallingLead] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [error, setError] = useState("");
  const [noteText, setNoteText] = useState("");
  const [scoring, setScoring] = useState(false);
  const [recomputingNba, setRecomputingNba] = useState(false);

  const fetchLead = useCallback(async () => {
    try {
      const data = await api.getLeadDetail(leadId);
      setLead(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load lead");
    }
  }, [leadId]);

  useEffect(() => {
    fetchLead();
    api.getLeadNBA(leadId).then(setNba).catch(() => {});
    api.getRepBriefResult(leadId).then(setBrief).catch(() => {});
    api.getLeadObjections(leadId).then(setObjections).catch(() => {});
    api.getLeadRecordings(leadId).then(setRecordings).catch(() => {});
    api.getLeadEnrichment(leadId).then(setEnrichment).catch(() => {});
  }, [fetchLead, leadId]);

  async function handleGenerateBrief() {
    setBriefLoading(true);
    try {
      await api.getRepBrief(leadId);
      // Poll for result after a short delay
      setTimeout(async () => {
        try {
          const result = await api.getRepBriefResult(leadId);
          setBrief(result);
        } catch { /* brief not ready yet */ }
        setBriefLoading(false);
      }, 3000);
    } catch {
      setBriefLoading(false);
    }
  }

  async function handleScore() {
    setScoring(true);
    try {
      await api.scoreLead(leadId);
      await fetchLead();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Score failed");
    } finally {
      setScoring(false);
    }
  }

  async function handleAddNote() {
    if (!noteText.trim()) return;
    try {
      await api.addNote(leadId, noteText);
      setNoteText("");
      await fetchLead();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Failed to add note");
    }
  }

  async function handleRecomputeNba() {
    setRecomputingNba(true);
    try {
      await api.recomputeNBA(leadId);
      const updated = await api.getLeadNBA(leadId);
      setNba(updated);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "NBA recompute failed");
    } finally {
      setRecomputingNba(false);
    }
  }

  async function handleEnqueueOutreach() {
    try {
      const res = await api.enqueueOutreach(leadId);
      alert(JSON.stringify(res, null, 2));
      await fetchLead();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Outreach failed");
    }
  }

  async function handlePlaceCall() {
    setCallingLead(true);
    try {
      await api.placeVoiceCall(leadId);
      setTimeout(async () => {
        const recs = await api.getLeadRecordings(leadId);
        setRecordings(recs);
        setCallingLead(false);
      }, 2000);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Call failed");
      setCallingLead(false);
    }
  }

  async function handleRunEnrichment() {
    setEnriching(true);
    try {
      await api.runEnrichment(leadId);
      setTimeout(async () => {
        const data = await api.getLeadEnrichment(leadId);
        setEnrichment(data);
        setEnriching(false);
      }, 3000);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Enrichment failed");
      setEnriching(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (!lead) {
    return <div className="animate-pulse text-gray-400">Loading lead...</div>;
  }

  const latestScore = lead.scores[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/leads" className="text-sm text-gray-500 hover:text-gray-700">&larr; Back to leads</Link>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">
            {lead.first_name || ""} {lead.last_name || "Unknown Lead"}
          </h1>
          <div className="mt-1 flex items-center gap-3">
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(lead.status)}`}>
              {lead.status.replace(/_/g, " ")}
            </span>
            {latestScore && (
              <span className="text-sm font-semibold text-gray-700">
                Score: {latestScore.total_score}/100
              </span>
            )}
            {lead.assigned_rep_name && (
              <span className="text-sm text-gray-500">
                Rep: {lead.assigned_rep_name}
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleScore}
            disabled={scoring}
            className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50"
          >
            {scoring ? "Scoring..." : "Score Lead"}
          </button>
          <button
            onClick={handlePlaceCall}
            disabled={callingLead}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {callingLead ? "Calling..." : "Voice Call"}
          </button>
          <button
            onClick={handleEnqueueOutreach}
            className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700"
          >
            Queue Outreach
          </button>
        </div>
      </div>

      {/* Quick Action Tabs */}
      <div className="flex gap-2">
        <Link
          href={`/leads/${leadId}/messages`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
          </svg>
          Messages
        </Link>
        <Link
          href={`/leads/${leadId}/qa`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          QA Reviews
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column — Property & Contact */}
        <div className="space-y-6 lg:col-span-2">
          {/* Property Card */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Details</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Address</span>
                <p className="font-medium">{lead.property.address_line1}</p>
                <p>{lead.property.city}, {lead.property.state} {lead.property.zip_code}</p>
              </div>
              <div>
                <span className="text-gray-500">County</span>
                <p className="font-medium">{lead.property.county}</p>
              </div>
              <div>
                <span className="text-gray-500">Type</span>
                <p className="font-medium">{lead.property.property_type}</p>
              </div>
              <div>
                <span className="text-gray-500">Year Built</span>
                <p className="font-medium">{lead.property.year_built ?? "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Roof Area</span>
                <p className="font-medium">
                  {lead.property.roof_area_sqft ? `${lead.property.roof_area_sqft.toLocaleString()} sqft` : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Assessed Value</span>
                <p className="font-medium">{formatCurrency(lead.property.assessed_value)}</p>
              </div>
              <div>
                <span className="text-gray-500">Utility Zone</span>
                <p className="font-medium">{lead.property.utility_zone ?? "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Existing Solar</span>
                <p className={cn("font-medium", lead.property.has_existing_solar ? "text-red-600" : "text-green-600")}>
                  {lead.property.has_existing_solar ? "Yes" : "No"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Owner Occupied</span>
                <p className="font-medium">{lead.property.owner_occupied ? "Yes" : "No"}</p>
              </div>
              <div>
                <span className="text-gray-500">Median Income</span>
                <p className="font-medium">{formatCurrency(lead.property.median_household_income)}</p>
              </div>
            </div>
          </div>

          {/* Score Breakdown */}
          {latestScore && (
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Score Breakdown ({latestScore.score_version})
              </h2>
              <div className="space-y-3">
                {[
                  { label: "Roof Age", score: latestScore.roof_age_score, max: 15 },
                  { label: "Ownership", score: latestScore.ownership_score, max: 15 },
                  { label: "Roof Area", score: latestScore.roof_area_score, max: 15 },
                  { label: "Home Value", score: latestScore.home_value_score, max: 10 },
                  { label: "Utility Rate", score: latestScore.utility_rate_score, max: 10 },
                  { label: "Shade", score: latestScore.shade_score, max: 10 },
                  { label: "Neighborhood", score: latestScore.neighborhood_score, max: 10 },
                  { label: "Income", score: latestScore.income_score, max: 8 },
                  { label: "Property Type", score: latestScore.property_type_score, max: 5 },
                  { label: "Existing Solar", score: latestScore.existing_solar_score, max: 2 },
                ].map(({ label, score, max }) => (
                  <div key={label} className="flex items-center gap-3">
                    <span className="w-28 text-sm text-gray-500">{label}</span>
                    <div className="flex-1 h-2 rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-solar-500"
                        style={{ width: `${(score / max) * 100}%` }}
                      />
                    </div>
                    <span className="w-12 text-right text-sm font-medium">
                      {score}/{max}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="font-bold text-lg">{latestScore.total_score}/100</span>
              </div>
            </div>
          )}

          {/* Outreach History */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Outreach History</h2>
            {lead.recent_outreach.length === 0 ? (
              <p className="text-gray-400 text-sm">No outreach attempts yet</p>
            ) : (
              <div className="space-y-2">
                {lead.recent_outreach.map((a) => (
                  <div key={a.id} className="flex items-center justify-between rounded-lg bg-gray-50 p-3">
                    <div className="flex items-center gap-3">
                      <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                        {a.channel}
                      </span>
                      <span className="text-sm text-gray-600">
                        {a.disposition ? a.disposition.replace(/_/g, " ") : "pending"}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDateTime(a.started_at)}
                      {a.duration_seconds != null && ` (${a.duration_seconds}s)`}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Voice Recordings */}
          {recordings.length > 0 && (
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Voice Recordings</h2>
              <div className="space-y-3">
                {recordings.map((r) => (
                  <div key={r.id} className="rounded-lg bg-gray-50 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                          {r.provider || "voice"}
                        </span>
                        <span className={cn(
                          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                          r.call_status === "completed" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-600"
                        )}>
                          {r.call_status || "unknown"}
                        </span>
                        {r.ai_sentiment && (
                          <span className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                            r.ai_sentiment === "positive" ? "bg-green-100 text-green-800" :
                            r.ai_sentiment === "negative" ? "bg-red-100 text-red-800" :
                            "bg-gray-100 text-gray-600"
                          )}>
                            {r.ai_sentiment}
                          </span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {formatDateTime(r.created_at)}
                        {r.duration_seconds != null && ` (${Math.floor(r.duration_seconds / 60)}:${String(r.duration_seconds % 60).padStart(2, "0")})`}
                      </span>
                    </div>
                    {r.recording_url && (
                      <audio controls className="w-full h-8" preload="none">
                        <source src={r.recording_url} type="audio/mpeg" />
                      </audio>
                    )}
                    {r.ai_summary && (
                      <p className="mt-2 text-xs text-gray-600 italic">{r.ai_summary}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Enrichment Data */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Contact Intelligence</h2>
              <button
                onClick={handleRunEnrichment}
                disabled={enriching}
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                {enriching ? "Running..." : "Enrich"}
              </button>
            </div>
            {enrichment?.validation && (
              <div className="mb-3 flex flex-wrap gap-2">
                {enrichment.validation.phone_valid !== null && (
                  <span className={cn(
                    "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
                    enrichment.validation.phone_valid ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  )}>
                    {enrichment.validation.phone_valid ? "Phone Valid" : "Phone Invalid"}
                  </span>
                )}
                {enrichment.validation.phone_type && (
                  <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700">
                    {enrichment.validation.phone_type}
                  </span>
                )}
                {enrichment.validation.email_valid !== null && (
                  <span className={cn(
                    "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
                    enrichment.validation.email_valid ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  )}>
                    {enrichment.validation.email_valid ? "Email Valid" : "Email Invalid"}
                  </span>
                )}
                {enrichment.validation.address_valid !== null && (
                  <span className={cn(
                    "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
                    enrichment.validation.address_valid ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                  )}>
                    {enrichment.validation.address_valid ? "Address Verified" : "Address Unverified"}
                  </span>
                )}
                {enrichment.validation.phone_carrier && (
                  <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                    {enrichment.validation.phone_carrier}
                  </span>
                )}
              </div>
            )}
            {enrichment?.enrichment && (
              <div className="space-y-2 text-sm">
                {enrichment.enrichment.job_title && (
                  <div>
                    <span className="text-gray-500">Job Title</span>
                    <p className="font-medium">{enrichment.enrichment.job_title}</p>
                  </div>
                )}
                {enrichment.enrichment.linkedin_url && (
                  <div>
                    <span className="text-gray-500">LinkedIn</span>
                    <p>
                      <a href={enrichment.enrichment.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-xs">
                        {enrichment.enrichment.linkedin_url}
                      </a>
                    </p>
                  </div>
                )}
                {enrichment.enrichment.emails && enrichment.enrichment.emails.length > 0 && (
                  <div>
                    <span className="text-gray-500">Discovered Emails</span>
                    {enrichment.enrichment.emails.map((e, i) => (
                      <p key={i} className="font-medium">{e.email} <span className="text-xs text-gray-400">({e.type})</span></p>
                    ))}
                  </div>
                )}
                <div className="pt-2 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-xs text-gray-400">
                    via {enrichment.enrichment.provider} | Confidence: {Math.round(enrichment.enrichment.confidence * 100)}%
                  </span>
                </div>
              </div>
            )}
            {!enrichment?.enrichment && !enrichment?.validation && (
              <p className="text-sm text-gray-400">Click &quot;Enrich&quot; to discover additional contact data.</p>
            )}
          </div>
        </div>

        {/* Right Column — NBA, Contact, Notes, Consent */}
        <div className="space-y-6">
          {/* Next Best Action */}
          {nba && (
            <div className="rounded-xl bg-purple-50 p-6 shadow-sm border border-purple-200">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold text-purple-900">Next Best Action</h2>
                <span className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                  nba.confidence >= 0.7 ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                )}>
                  {Math.round(nba.confidence * 100)}% confident
                </span>
              </div>
              <div className="mb-3">
                <p className="text-xl font-bold text-purple-800 capitalize">
                  {nba.recommended_action.replace(/_/g, " ")}
                </p>
                {nba.recommended_channel && (
                  <p className="text-sm text-purple-600 mt-0.5">
                    via <span className="font-medium uppercase">{nba.recommended_channel}</span>
                    {nba.schedule_time && ` at ${formatDateTime(nba.schedule_time)}`}
                  </p>
                )}
              </div>
              {nba.reason_codes && nba.reason_codes.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-1">
                  {nba.reason_codes.map((code, i) => (
                    <span key={i} className="inline-flex items-center rounded-full bg-purple-100 px-2 py-0.5 text-xs text-purple-700">
                      {code}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <button
                  onClick={handleEnqueueOutreach}
                  className="flex-1 rounded-lg bg-purple-600 px-3 py-2 text-sm font-medium text-white hover:bg-purple-700"
                >
                  Apply Action
                </button>
                <button
                  onClick={handleRecomputeNba}
                  disabled={recomputingNba}
                  className="rounded-lg border border-purple-300 bg-white px-3 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-50"
                >
                  {recomputingNba ? "..." : "Refresh"}
                </button>
              </div>
            </div>
          )}

          {/* AI Brief */}
          <div className="rounded-xl bg-blue-50 p-6 shadow-sm border border-blue-200">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-blue-900 flex items-center gap-2">
                <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
                AI Brief
              </h2>
              <button
                onClick={handleGenerateBrief}
                disabled={briefLoading}
                className="rounded-lg border border-blue-300 bg-white px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50 disabled:opacity-50"
              >
                {briefLoading ? "Generating..." : brief ? "Refresh" : "Generate"}
              </button>
            </div>
            {brief ? (
              <div className="space-y-3 text-sm">
                <p className="text-blue-800">{brief.summary}</p>
                {brief.talk_track.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-blue-700 mb-1">Talk Track</p>
                    <ul className="space-y-1">
                      {brief.talk_track.map((t, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-blue-700">
                          <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-blue-400" />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {brief.objection_handlers.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-blue-700 mb-1">Objection Handlers</p>
                    <ul className="space-y-1">
                      {brief.objection_handlers.map((h, i) => (
                        <li key={i} className="text-blue-700 text-xs bg-blue-100 rounded px-2 py-1">{h}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <p className="text-xs text-blue-600 italic">{brief.recommended_approach}</p>
              </div>
            ) : (
              <p className="text-sm text-blue-600">Click &quot;Generate&quot; to create an AI brief for this lead.</p>
            )}
          </div>

          {/* Objections */}
          {objections.length > 0 && (
            <div className="rounded-xl bg-amber-50 p-6 shadow-sm border border-amber-200">
              <h2 className="text-lg font-semibold text-amber-900 mb-3">Objections Detected</h2>
              <div className="space-y-2">
                {objections.map((o) => (
                  <div key={o.id} className="flex items-center justify-between rounded-lg bg-amber-100 p-2.5">
                    <div>
                      <span className="text-sm font-medium text-amber-800">{o.tag.replace(/_/g, " ")}</span>
                      {o.evidence_span && (
                        <p className="text-xs text-amber-600 mt-0.5 italic">&quot;{o.evidence_span}&quot;</p>
                      )}
                    </div>
                    <span className="text-xs font-medium text-amber-700">
                      {Math.round(o.confidence * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Contact Info */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact</h2>
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-gray-500">Phone</span>
                <p className="font-medium">{lead.phone || "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Email</span>
                <p className="font-medium">{lead.email || "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Last Contacted</span>
                <p className="font-medium">
                  {lead.last_contacted_at ? formatDateTime(lead.last_contacted_at) : "Never"}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-200">
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">{lead.total_call_attempts}</p>
                  <p className="text-xs text-gray-500">Calls</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">{lead.total_sms_sent}</p>
                  <p className="text-xs text-gray-500">SMS</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">{lead.total_emails_sent}</p>
                  <p className="text-xs text-gray-500">Emails</p>
                </div>
              </div>
            </div>
          </div>

          {/* Notes */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Notes</h2>
            <div className="space-y-3 mb-4">
              {lead.notes.length === 0 ? (
                <p className="text-gray-400 text-sm">No notes yet</p>
              ) : (
                lead.notes.map((n) => (
                  <div key={n.id} className="rounded-lg bg-gray-50 p-3">
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{n.author}</span>
                      <span>{formatDateTime(n.created_at)}</span>
                    </div>
                    <p className="mt-1 text-sm text-gray-700">{n.content}</p>
                  </div>
                ))
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Add a note..."
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
                onKeyDown={(e) => e.key === "Enter" && handleAddNote()}
              />
              <button
                onClick={handleAddNote}
                className="rounded-lg bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-700"
              >
                Add
              </button>
            </div>
          </div>

          {/* Consent Logs */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Consent History</h2>
            {lead.consent_logs.length === 0 ? (
              <p className="text-gray-400 text-sm">No consent records</p>
            ) : (
              <div className="space-y-2">
                {lead.consent_logs.map((c) => (
                  <div key={c.id} className="flex items-center justify-between rounded-lg bg-gray-50 p-3 text-sm">
                    <div>
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        c.status === "opted_in" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      )}>
                        {c.status.replace(/_/g, " ")}
                      </span>
                      <span className="ml-2 text-gray-600">{c.consent_type.replace(/_/g, " ")}</span>
                    </div>
                    <span className="text-xs text-gray-500">{formatDate(c.recorded_at)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
