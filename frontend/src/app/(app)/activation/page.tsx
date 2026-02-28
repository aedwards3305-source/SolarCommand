"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { leadgenApi } from "@/lib/api/leadgen";
import type { ActivationRow, ActivationFilters } from "@/lib/types/leadgen";

const COUNTIES = [
  "Baltimore County",
  "Howard County",
  "Anne Arundel County",
  "Montgomery County",
  "Prince George's County",
];

function scoreBadge(score: number | null) {
  if (score == null) return { label: "—", cls: "bg-gray-100 text-gray-600" };
  if (score >= 75) return { label: `${score}`, cls: "bg-red-100 text-red-800" };
  if (score >= 50) return { label: `${score}`, cls: "bg-orange-100 text-orange-800" };
  return { label: `${score}`, cls: "bg-blue-100 text-blue-800" };
}

export default function ActivationQueuePage() {
  const router = useRouter();
  const [leads, setLeads] = useState<ActivationRow[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [batchMsg, setBatchMsg] = useState("");
  const [batchMsgError, setBatchMsgError] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Filters
  const [county, setCounty] = useState("");
  const [minScore, setMinScore] = useState(50);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const filters: ActivationFilters = {};
      if (county) filters.county = county;
      if (minScore > 0) filters.min_discovery_score = minScore;
      const res = await leadgenApi.listActivationQueue(filters);
      setLeads(res.leads);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [county, minScore]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleAll() {
    if (selected.size === leads.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(leads.map((l) => l.id)));
    }
  }

  async function handleBatchActivate() {
    if (selected.size === 0) return;
    setProcessing(true);
    setBatchMsg("");
    setBatchMsgError(false);
    try {
      // Filter out any DNC-flagged leads
      const safeIds = leads
        .filter((l) => selected.has(l.id) && l.dnc_status === "clear")
        .map((l) => l.id);
      const flagged = selected.size - safeIds.length;

      if (safeIds.length === 0) {
        setBatchMsg("All selected leads are DNC-flagged. Cannot activate.");
        setBatchMsgError(true);
        setProcessing(false);
        return;
      }

      const res = await leadgenApi.approveActivation(safeIds);
      setBatchMsg(
        `${res.activated} lead${res.activated !== 1 ? "s" : ""} activated` +
        (flagged > 0 ? ` (${flagged} DNC-flagged skipped)` : "")
      );
      setSelected(new Set());
      fetchQueue();
    } catch (e) {
      setBatchMsg(e instanceof Error ? e.message : "Batch activation failed");
      setBatchMsgError(true);
    } finally {
      setProcessing(false);
      setTimeout(() => setBatchMsg(""), 5000);
    }
  }

  async function handleReject(id: string) {
    if (!rejectReason.trim()) return;
    try {
      await leadgenApi.rejectActivation(id, rejectReason.trim());
      setRejectingId(null);
      setRejectReason("");
      fetchQueue();
    } catch (e) {
      setBatchMsg(e instanceof Error ? e.message : "Rejection failed");
      setBatchMsgError(true);
    }
  }

  const allSelected = leads.length > 0 && selected.size === leads.length;
  const clearCount = leads.filter((l) => selected.has(l.id) && l.dnc_status === "clear").length;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Activation Queue</h1>
          <p className="mt-1 text-sm text-gray-500">
            Review and activate discovered leads with verified contacts
          </p>
        </div>
        <div className="flex items-center gap-3">
          {batchMsg && (
            <span className={cn(
              "text-sm rounded-lg px-3 py-1.5",
              batchMsgError ? "text-red-700 bg-red-50" : "text-green-700 bg-green-50"
            )}>{batchMsg}</span>
          )}
          <button
            onClick={handleBatchActivate}
            disabled={processing || selected.size === 0}
            className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50"
          >
            {processing
              ? "Activating..."
              : `Activate Selected (${clearCount})`}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Filters */}
      <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">County</label>
            <select
              value={county}
              onChange={(e) => setCounty(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
            >
              <option value="">All Counties</option>
              {COUNTIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Min Discovery Score: {minScore}
            </label>
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-32 accent-solar-600"
              aria-label="Minimum discovery score filter"
            />
          </div>
          <button
            onClick={() => { setCounty(""); setMinScore(50); }}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Reset
          </button>
        </div>
      </div>

      {/* Queue Table */}
      <div className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400 animate-pulse">Loading activation queue...</div>
        ) : leads.length === 0 ? (
          <div className="p-8 text-center text-gray-400">No leads ready for activation</div>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="rounded border-gray-300 text-solar-600 focus:ring-solar-500"
                    aria-label="Select all leads"
                  />
                </th>
                <th className="px-3 py-3 text-left">Address</th>
                <th className="px-3 py-3 text-left">Score</th>
                <th className="px-3 py-3 text-left">Contact</th>
                <th className="px-3 py-3 text-left">Confidence</th>
                <th className="px-3 py-3 text-left">DNC</th>
                <th className="px-3 py-3 text-left">Consent</th>
                <th className="px-3 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {leads.map((lead) => {
                const badge = scoreBadge(lead.discovery_score);
                const isExpanded = expandedId === lead.id;
                return (
                  <tr key={lead.id} className="group">
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        checked={selected.has(lead.id)}
                        onChange={() => toggleSelect(lead.id)}
                        className="rounded border-gray-300 text-solar-600 focus:ring-solar-500"
                        aria-label={`Select ${lead.address}`}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : lead.id)}
                        className="text-left"
                      >
                        <span className="font-medium text-gray-900 hover:text-solar-600">
                          {lead.address}
                        </span>
                        <p className="text-xs text-gray-500">
                          {lead.city}, {lead.state}
                          {lead.county ? ` — ${lead.county}` : ""}
                        </p>
                      </button>
                      {isExpanded && (
                        <div className="mt-2 rounded-lg bg-gray-50 p-3 text-xs text-gray-600 space-y-1">
                          <p><span className="font-medium">Owner:</span> {lead.owner_name ?? "—"}</p>
                          <p><span className="font-medium">Type:</span> {lead.property_type?.replace(/_/g, " ") ?? "—"}</p>
                          <p><span className="font-medium">Year Built:</span> {lead.year_built ?? "—"}</p>
                          <p><span className="font-medium">Utility:</span> {lead.utility_name ?? "—"}</p>
                          <p>
                            <span className="font-medium">Sources:</span>{" "}
                            {lead.source_types.map((s) => s.replace(/_/g, " ")).join(", ")}
                          </p>
                          <div className="pt-1">
                            <button
                              onClick={() => router.push(`/discovery/${lead.id}`)}
                              className="text-solar-600 hover:text-solar-700 font-medium"
                            >
                              View Full Detail →
                            </button>
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <span className={cn("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", badge.cls)}>
                        {badge.label}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <div className="text-gray-900">{lead.best_phone ?? "—"}</div>
                      {lead.best_phone_type && (
                        <span className="text-xs text-gray-500">{lead.best_phone_type}</span>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      {lead.best_contact_confidence != null ? (
                        <span
                          className={cn(
                            "text-sm font-medium",
                            lead.best_contact_confidence >= 0.8
                              ? "text-green-700"
                              : lead.best_contact_confidence >= 0.6
                              ? "text-yellow-700"
                              : "text-red-700"
                          )}
                        >
                          {Math.round(lead.best_contact_confidence * 100)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                          lead.dnc_status === "clear"
                            ? "bg-green-100 text-green-800"
                            : "bg-red-100 text-red-800"
                        )}
                      >
                        {lead.dnc_status === "clear" ? "Clear" : "Flagged"}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                          lead.consent_status === "explicit_opt_in"
                            ? "bg-green-100 text-green-800"
                            : "bg-yellow-100 text-yellow-800"
                        )}
                      >
                        {lead.consent_status.replace(/_/g, " ")}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right">
                      {rejectingId === lead.id ? (
                        <div className="flex items-center gap-1">
                          <input
                            type="text"
                            value={rejectReason}
                            onChange={(e) => setRejectReason(e.target.value)}
                            placeholder="Reason..."
                            className="w-28 rounded border border-gray-300 px-2 py-1 text-xs focus:ring-1 focus:ring-solar-500 outline-none"
                            autoFocus
                            onKeyDown={(e) => { if (e.key === "Escape") { setRejectingId(null); setRejectReason(""); } }}
                          />
                          <button
                            onClick={() => handleReject(lead.id)}
                            disabled={!rejectReason.trim()}
                            className="rounded bg-red-600 px-2 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-50"
                          >
                            Confirm
                          </button>
                          <button
                            onClick={() => { setRejectingId(null); setRejectReason(""); }}
                            className="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex justify-end gap-1">
                          <button
                            onClick={() => router.push(`/discovery/${lead.id}`)}
                            className="rounded border border-gray-300 bg-white px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
                          >
                            View
                          </button>
                          <button
                            onClick={() => { setRejectingId(lead.id); setRejectReason(""); }}
                            className="rounded border border-red-200 bg-white px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}

        {/* Footer */}
        <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 flex items-center justify-between text-sm">
          <span className="text-gray-500">
            {total} lead{total !== 1 ? "s" : ""} ready for activation
          </span>
          <span className="text-gray-500">
            {selected.size} selected ({clearCount} clear for activation)
          </span>
        </div>
      </div>
    </div>
  );
}
