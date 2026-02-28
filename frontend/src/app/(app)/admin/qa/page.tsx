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

  const scoreColor = (score: number) => {
    if (score >= 80) return "text-green-700";
    if (score >= 60) return "text-yellow-700";
    return "text-red-700";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">QA Review Queue</h1>
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={flaggedOnly}
            onChange={(e) => { setFlaggedOnly(e.target.checked); setPage(1); }}
            className="rounded border-gray-300"
          />
          Flagged only
        </label>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Lead</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Score</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Flags</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Reviewer</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No QA reviews found</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/leads/${item.lead_id}/qa`} className="font-medium text-solar-600 hover:text-solar-800">
                      {item.lead_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn("text-lg font-bold", scoreColor(item.compliance_score))}>
                      {item.compliance_score}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                      item.checklist_pass ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                    )}>
                      {item.checklist_pass ? "PASS" : "FAIL"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {item.flags && item.flags.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {item.flags.slice(0, 3).map((f, i) => (
                          <span key={i} className={cn(
                            "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-medium",
                            f.severity === "critical" ? "bg-red-100 text-red-700" :
                            f.severity === "warning" ? "bg-yellow-100 text-yellow-700" :
                            "bg-blue-100 text-blue-700"
                          )}>
                            {f.flag.slice(0, 25)}
                          </span>
                        ))}
                        {item.flags.length > 3 && (
                          <span className="text-xs text-gray-400">+{item.flags.length - 3}</span>
                        )}
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">None</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{item.reviewed_by}</td>
                  <td className="px-4 py-3 text-xs text-gray-500">{formatDateTime(item.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page === 1}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-sm text-gray-500">Page {page}</span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={items.length < 50}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
