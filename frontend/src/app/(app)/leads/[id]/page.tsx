"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { statusColor, formatDate, formatDateTime, formatCurrency, cn } from "@/lib/utils";

type LeadDetail = Awaited<ReturnType<typeof api.getLeadDetail>>;

export default function LeadDetailPage() {
  const params = useParams();
  const leadId = Number(params.id);
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [error, setError] = useState("");
  const [noteText, setNoteText] = useState("");
  const [scoring, setScoring] = useState(false);

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
  }, [fetchLead]);

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

  async function handleEnqueueOutreach() {
    try {
      const res = await api.enqueueOutreach(leadId);
      alert(JSON.stringify(res, null, 2));
      await fetchLead();
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Outreach failed");
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
            onClick={handleEnqueueOutreach}
            className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700"
          >
            Queue Outreach
          </button>
        </div>
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
        </div>

        {/* Right Column — Contact, Notes, Consent */}
        <div className="space-y-6">
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
