"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { cn, formatDateTime } from "@/lib/utils";

interface QAItem {
  id: number;
  lead_id: number;
  lead_name: string;
  conversation_id: number | null;
  compliance_score: number;
  flags: Array<{ flag: string; severity: string }> | null;
  checklist_pass: boolean;
  reviewed_by: string;
  created_at: string;
}

function ScoreRing({ score }: { score: number }) {
  const color =
    score >= 80 ? "text-emerald-600" : score >= 60 ? "text-amber-500" : "text-red-500";
  const bg =
    score >= 80 ? "bg-emerald-50" : score >= 60 ? "bg-amber-50" : "bg-red-50";
  return (
    <span className={cn("inline-flex items-center justify-center h-9 w-9 rounded-full text-sm font-bold tabular-nums", bg, color)}>
      {score}
    </span>
  );
}

export default function QAQueuePage() {
  const [items, setItems] = useState<QAItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [flaggedOnly, setFlaggedOnly] = useState(false);

  const fetchQueue = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(page), page_size: "50" };
      if (flaggedOnly) params.flagged_only = "true";
      const data = await api.getQAQueue(params);
      setItems(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load QA queue");
    } finally {
      setLoading(false);
    }
  }, [page, flaggedOnly]);

  useEffect(() => {
    fetchQueue();
  }, [fetchQueue]);

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="admin-toolbar">
        <label className="flex items-center gap-2 text-sm text-gray-500 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={flaggedOnly}
            onChange={(e) => { setFlaggedOnly(e.target.checked); setPage(1); }}
            className="rounded border-gray-300 text-solar-600 focus:ring-solar-500"
          />
          Flagged only
        </label>
        <span className="ml-auto text-xs font-medium text-gray-400">
          Page {page}
        </span>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="admin-card">
        <div className="overflow-x-auto">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Lead</th>
                <th>Score</th>
                <th>Status</th>
                <th>Flags</th>
                <th>Reviewer</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
                    <p className="mt-3 text-sm text-gray-400">Loading...</p>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400 text-sm">No QA reviews found</td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <Link
                        href={`/leads/${item.lead_id}/qa`}
                        className="font-medium text-solar-600 hover:text-solar-800 transition-colors"
                      >
                        {item.lead_name}
                      </Link>
                    </td>
                    <td>
                      <ScoreRing score={item.compliance_score} />
                    </td>
                    <td>
                      <span
                        className={cn(
                          "admin-badge",
                          item.checklist_pass
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-red-50 text-red-700"
                        )}
                      >
                        {item.checklist_pass ? "PASS" : "FAIL"}
                      </span>
                    </td>
                    <td>
                      {item.flags && item.flags.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {item.flags.slice(0, 3).map((f, i) => (
                            <span
                              key={i}
                              className={cn(
                                "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium ring-1 ring-inset",
                                f.severity === "critical"
                                  ? "bg-red-50 text-red-600 ring-red-500/20"
                                  : f.severity === "warning"
                                  ? "bg-amber-50 text-amber-600 ring-amber-500/20"
                                  : "bg-blue-50 text-blue-600 ring-blue-500/20"
                              )}
                            >
                              {f.flag.slice(0, 25)}
                            </span>
                          ))}
                          {item.flags.length > 3 && (
                            <span className="text-[11px] text-gray-400 self-center">+{item.flags.length - 3}</span>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-gray-300">None</span>
                      )}
                    </td>
                    <td className="text-sm text-gray-500">{item.reviewed_by}</td>
                    <td className="text-xs text-gray-400 tabular-nums">{formatDateTime(item.created_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="admin-pagination">
        <span className="text-xs text-gray-400">Page {page}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="admin-page-btn"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(page + 1)}
            disabled={items.length < 50}
            className="admin-page-btn"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
