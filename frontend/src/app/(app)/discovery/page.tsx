"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";
import { leadgenApi } from "@/lib/api/leadgen";
import type {
  DiscoveredLeadRow,
  DiscoveryFilters,
  DiscoveryStatus,
} from "@/lib/types/leadgen";

const DiscoveryMap = dynamic(
  () => import("@/components/discovery/DiscoveryMap"),
  { ssr: false, loading: () => <div className="h-full w-full animate-pulse rounded-xl bg-gray-100" /> }
);

const COUNTIES = [
  "Baltimore County",
  "Howard County",
  "Anne Arundel County",
  "Montgomery County",
  "Prince George's County",
];

function scoreBadge(score: number | null) {
  if (score == null) return { label: "—", cls: "bg-gray-100 text-gray-600" };
  if (score >= 75) return { label: `${score} Hot`, cls: "bg-red-100 text-red-800" };
  if (score >= 50) return { label: `${score} Warm`, cls: "bg-orange-100 text-orange-800" };
  return { label: `${score} Cool`, cls: "bg-blue-100 text-blue-800" };
}

export default function DiscoveryPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<DiscoveredLeadRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState("");
  const [discovering, setDiscovering] = useState(false);
  const [showDiscoverPicker, setShowDiscoverPicker] = useState(false);
  const [pipelining, setPipelining] = useState(false);
  const [showPipelinePicker, setShowPipelinePicker] = useState(false);
  const [error, setError] = useState("");

  // Filters
  const [county, setCounty] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [maxScore, setMaxScore] = useState(100);
  const [status, setStatus] = useState<DiscoveryStatus | "">("");
  const [hasPermit, setHasPermit] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // Selected lead popup from map
  const [selectedLead, setSelectedLead] = useState<DiscoveredLeadRow | null>(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const filters: DiscoveryFilters = {
        page,
        page_size: pageSize,
      };
      if (county) filters.county = county;
      if (minScore > 0) filters.min_score = minScore;
      if (maxScore < 100) filters.max_score = maxScore;
      if (status) filters.status = status;
      if (hasPermit) filters.has_permit = true;

      const res = await leadgenApi.listDiscoveredLeads(filters);
      setLeads(res.leads);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [county, minScore, maxScore, status, hasPermit, page]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  async function handleSkipTrace() {
    setEnriching(true);
    setEnrichMsg("");
    try {
      const res = await leadgenApi.skipTrace(50, {
        county: county || undefined,
        min_score: minScore > 0 ? minScore : undefined,
      });
      setEnrichMsg(
        `Skip-trace complete: ${res.found} phones found, ${res.activated} auto-activated`
      );
      fetchLeads();
    } catch (e) {
      setEnrichMsg(e instanceof Error ? e.message : "Skip-trace failed");
    } finally {
      setEnriching(false);
      setTimeout(() => setEnrichMsg(""), 6000);
    }
  }

  async function handleRunDiscovery(selectedCounty: string) {
    setDiscovering(true);
    setEnrichMsg("");
    setShowDiscoverPicker(false);
    try {
      const res = await leadgenApi.runDiscovery(selectedCounty, 1000);
      setEnrichMsg(
        `Discovery complete: ${res.ingested} ingested, ${res.scored} scored, ${res.skipped} skipped`
      );
      fetchLeads();
    } catch (e) {
      setEnrichMsg(e instanceof Error ? e.message : "Discovery failed");
    } finally {
      setDiscovering(false);
      setTimeout(() => setEnrichMsg(""), 8000);
    }
  }

  async function handleFullPipeline(selectedCounty: string) {
    setPipelining(true);
    setEnrichMsg("");
    setShowPipelinePicker(false);
    try {
      const res = await leadgenApi.runFullPipeline(selectedCounty);
      setEnrichMsg(
        `Pipeline done: ${res.discovered} new leads, ${res.phones_found} phones found, ${res.activated} activated`
      );
      fetchLeads();
    } catch (e) {
      setEnrichMsg(e instanceof Error ? e.message : "Pipeline failed");
    } finally {
      setPipelining(false);
      setTimeout(() => setEnrichMsg(""), 10000);
    }
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Discovery Dashboard</h1>
        <div className="flex items-center gap-3">
          {enrichMsg && (
            <span className="text-sm text-green-700 bg-green-50 rounded-lg px-3 py-1.5">
              {enrichMsg}
            </span>
          )}
          {/* Full Pipeline — one click does everything */}
          <div className="relative">
            <button
              onClick={() => setShowPipelinePicker(!showPipelinePicker)}
              disabled={pipelining || discovering}
              className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50"
            >
              {pipelining ? "Running Pipeline..." : "Full Pipeline"}
            </button>
            {showPipelinePicker && (
              <div className="absolute right-0 top-full mt-1 z-50 w-56 rounded-lg bg-white shadow-lg border border-gray-200 py-1">
                <p className="px-4 py-2 text-xs text-gray-500 border-b border-gray-100">
                  Discover + Tracerfy + Auto-Activate
                </p>
                {COUNTIES.map((c) => (
                  <button
                    key={c}
                    onClick={() => handleFullPipeline(c)}
                    className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>
          {/* Individual steps (advanced) */}
          <div className="relative">
            <button
              onClick={() => setShowDiscoverPicker(!showDiscoverPicker)}
              disabled={discovering || pipelining}
              className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
            >
              {discovering ? "Discovering..." : "Discover Only"}
            </button>
            {showDiscoverPicker && (
              <div className="absolute right-0 top-full mt-1 z-50 w-56 rounded-lg bg-white shadow-lg border border-gray-200 py-1">
                {COUNTIES.map((c) => (
                  <button
                    key={c}
                    onClick={() => handleRunDiscovery(c)}
                    className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            onClick={handleSkipTrace}
            disabled={enriching || pipelining}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {enriching ? "Tracing..." : "Skip Trace Top 50"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Filter bar */}
      <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">County</label>
            <select
              value={county}
              onChange={(e) => { setCounty(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
            >
              <option value="">All Counties</option>
              {COUNTIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Min Score: {minScore}</label>
            <input type="range" min={0} max={100} value={minScore} onChange={(e) => { setMinScore(Number(e.target.value)); setPage(1); }} className="w-32 accent-solar-600" aria-label="Minimum score filter" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Max Score: {maxScore}</label>
            <input type="range" min={0} max={100} value={maxScore} onChange={(e) => { setMaxScore(Number(e.target.value)); setPage(1); }} className="w-32 accent-solar-600" aria-label="Maximum score filter" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
            <select value={status} onChange={(e) => { setStatus(e.target.value as DiscoveryStatus | ""); setPage(1); }} className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none">
              <option value="">All</option>
              <option value="discovered">Discovered</option>
              <option value="scored">Scored</option>
              <option value="enriched">Enriched</option>
              <option value="activation_ready">Activation Ready</option>
              <option value="activated">Activated</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-700 pb-2">
            <input type="checkbox" checked={hasPermit} onChange={(e) => { setHasPermit(e.target.checked); setPage(1); }} className="rounded border-gray-300 text-solar-600 focus:ring-solar-500" />
            Has Permit
          </label>
          <button onClick={() => { setCounty(""); setMinScore(0); setMaxScore(100); setStatus(""); setHasPermit(false); setPage(1); }} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-600 hover:bg-gray-50">
            Reset Filters
          </button>
        </div>
      </div>

      {/* Main content: map + list */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2" style={{ minHeight: "500px" }}>
        {/* Map */}
        <div className="h-[500px] xl:h-auto">
          <DiscoveryMap leads={leads} onSelectLead={setSelectedLead} />
          {/* Map popup */}
          {selectedLead && (
            <div className="mt-2 rounded-xl bg-white p-4 shadow-sm border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-semibold text-gray-900">{selectedLead.address}</p>
                  <p className="text-sm text-gray-500">
                    {selectedLead.city}, {selectedLead.state} — {selectedLead.county}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedLead(null)}
                  className="text-gray-400 hover:text-gray-600"
                  aria-label="Close popup"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="mt-2 flex items-center gap-2 text-sm">
                {(() => {
                  const b = scoreBadge(selectedLead.discovery_score);
                  return (
                    <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", b.cls)}>
                      {b.label}
                    </span>
                  );
                })()}
                <span className="text-gray-500">{selectedLead.property_type}</span>
                {selectedLead.year_built && (
                  <span className="text-gray-500">Built {selectedLead.year_built}</span>
                )}
                {selectedLead.has_permit && (
                  <span className="rounded-full bg-green-100 text-green-800 px-2 py-0.5 text-xs font-medium">
                    Permit
                  </span>
                )}
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => router.push(`/discovery/${selectedLead.id}`)}
                  className="rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700"
                >
                  View Detail
                </button>
              </div>
            </div>
          )}
        </div>

        {/* List */}
        <div className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden flex flex-col">
          <div className="flex-1 overflow-auto">
            {loading ? (
              <div className="p-8 text-center text-gray-400 animate-pulse">Loading discovered leads...</div>
            ) : leads.length === 0 ? (
              <div className="p-8 text-center text-gray-400">No leads match filters</div>
            ) : (
              <table className="min-w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <tr>
                    <th className="px-4 py-3 text-left">Address</th>
                    <th className="px-3 py-3 text-left">Score</th>
                    <th className="px-3 py-3 text-left">Type</th>
                    <th className="px-3 py-3 text-left">Utility</th>
                    <th className="px-3 py-3 text-left">Sources</th>
                    <th className="px-3 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {leads.map((lead) => {
                    const badge = scoreBadge(lead.discovery_score);
                    return (
                      <tr key={lead.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <button
                            onClick={() => router.push(`/discovery/${lead.id}`)}
                            className="font-medium text-gray-900 hover:text-solar-600 text-left"
                          >
                            {lead.address}
                          </button>
                          <p className="text-xs text-gray-500">
                            {lead.city}, {lead.state}
                            {lead.county ? ` — ${lead.county}` : ""}
                          </p>
                        </td>
                        <td className="px-3 py-3">
                          <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", badge.cls)}>
                            {badge.label}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-gray-600">
                          {lead.property_type?.replace(/_/g, " ") ?? "—"}
                          {lead.year_built ? (
                            <span className="block text-xs text-gray-400">{lead.year_built}</span>
                          ) : null}
                        </td>
                        <td className="px-3 py-3 text-gray-600">
                          {lead.utility_name ?? "—"}
                          {lead.has_existing_solar && (
                            <span className="block text-xs text-red-500">Has solar</span>
                          )}
                        </td>
                        <td className="px-3 py-3">
                          <div className="flex flex-wrap gap-1">
                            {lead.source_types.map((s) => (
                              <span
                                key={s}
                                className="inline-flex rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600"
                              >
                                {s.replace(/_/g, " ")}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-3 py-3 text-right">
                          <div className="flex justify-end gap-1">
                            <button
                              onClick={() => router.push(`/discovery/${lead.id}`)}
                              className="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                            >
                              View
                            </button>
                            {lead.status === "activation_ready" && (
                              <button
                                onClick={() => router.push(`/discovery/${lead.id}`)}
                                className="rounded bg-solar-600 px-2 py-1 text-xs text-white hover:bg-solar-700"
                              >
                                Activate
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination */}
          {total > 0 && (
          <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 flex items-center justify-between text-sm">
            <span className="text-gray-500">
              Showing {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, total)} of{" "}
              {total.toLocaleString()}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded border border-gray-300 bg-white px-3 py-1 text-gray-700 hover:bg-gray-50 disabled:opacity-40"
              >
                Prev
              </button>
              <span className="flex items-center text-gray-500">
                {page} / {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded border border-gray-300 bg-white px-3 py-1 text-gray-700 hover:bg-gray-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
          )}
        </div>
      </div>

    </div>
  );
}
