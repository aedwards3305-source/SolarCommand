"use client";

import { useEffect, useState } from "react";
import { cn, formatDateTime, formatCostUsd } from "@/lib/utils";
import { api } from "@/lib/api";

interface CostSummary {
  month: string;
  total_cost: number;
  ai_cost: number;
  voice_cost: number;
  ai_run_count: number;
  voice_call_count: number;
  daily_totals: Array<{ date: string; ai_cost: number; voice_cost: number }>;
}

interface CostItem {
  id: string;
  category: string;
  timestamp: string;
  description: string;
  lead_id: number | null;
  detail: string;
  cost_usd: number;
}

function getMonthOptions(): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [];
  const now = new Date();
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const label = d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
    options.push({ value, label });
  }
  return options;
}

const CHART_H = 128;

export default function CostCenterPage() {
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [items, setItems] = useState<CostItem[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [month, setMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });
  const [category, setCategory] = useState("all");
  const [page, setPage] = useState(0);

  // Reset page when filters change
  useEffect(() => {
    setPage(0);
  }, [month, category]);

  useEffect(() => {
    setLoading(true);
    setError("");

    const summaryParams: Record<string, string> = { month };
    const itemParams: Record<string, string> = {
      month,
      category,
      limit: "50",
      offset: String(page * 50),
    };

    Promise.all([api.getCostSummary(summaryParams), api.getCostItems(itemParams)])
      .then(([summaryData, itemsData]) => {
        setSummary(summaryData);
        setItems(itemsData.items);
        setTotal(itemsData.total);
        setHasMore(itemsData.has_more);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [month, category, page]);

  const maxDailyCost = summary
    ? Math.max(...summary.daily_totals.map((d) => d.ai_cost + d.voice_cost), 0.01)
    : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cost Center</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monthly breakdown of AI and voice call costs
          </p>
        </div>
        <select
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
        >
          {getMonthOptions().map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Total Cost</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {summary ? formatCostUsd(summary.total_cost) : "—"}
          </p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">AI Cost</p>
          <p className="mt-1 text-2xl font-bold text-indigo-600">
            {summary ? formatCostUsd(summary.ai_cost) : "—"}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">
            {summary ? `${summary.ai_run_count.toLocaleString()} runs` : ""}
          </p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Voice Cost</p>
          <p className="mt-1 text-2xl font-bold text-green-600">
            {summary ? formatCostUsd(summary.voice_cost) : "—"}
          </p>
          <p className="text-xs text-gray-400 mt-0.5">
            {summary ? `${summary.voice_call_count.toLocaleString()} calls` : ""}
          </p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Transactions</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {summary
              ? (summary.ai_run_count + summary.voice_call_count).toLocaleString()
              : "—"}
          </p>
        </div>
      </div>

      {/* Daily Spending Chart — pixel-based bars */}
      {summary && summary.daily_totals.length > 0 && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Daily Spending</h3>
          <div
            className="flex items-end gap-[2px]"
            style={{ height: `${CHART_H}px` }}
          >
            {summary.daily_totals.map((day) => {
              const dayTotal = day.ai_cost + day.voice_cost;
              const barH = Math.max(
                Math.round((dayTotal / maxDailyCost) * CHART_H),
                dayTotal > 0 ? 2 : 0
              );
              const aiH =
                dayTotal > 0 ? Math.round((day.ai_cost / dayTotal) * barH) : 0;
              const voiceH = barH - aiH;
              return (
                <div
                  key={day.date}
                  className="flex-1 relative group"
                  style={{ height: `${CHART_H}px` }}
                >
                  {/* Bar anchored to bottom */}
                  <div
                    className="absolute bottom-0 left-0 right-0 flex flex-col rounded-t-sm overflow-hidden"
                    style={{ height: `${barH}px` }}
                  >
                    {aiH > 0 && (
                      <div
                        className="w-full bg-indigo-400"
                        style={{ height: `${aiH}px` }}
                      />
                    )}
                    {voiceH > 0 && (
                      <div
                        className="w-full bg-green-400"
                        style={{ height: `${voiceH}px` }}
                      />
                    )}
                  </div>
                  {/* Hover tooltip */}
                  {dayTotal > 0 && (
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block bg-gray-900 text-white text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap z-10 pointer-events-none">
                      {formatCostUsd(dayTotal)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-gray-400">
            <span>{summary.daily_totals[0]?.date.slice(5)}</span>
            <span>
              {summary.daily_totals[summary.daily_totals.length - 1]?.date.slice(5)}
            </span>
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-indigo-400" />
              AI
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-green-400" />
              Voice
            </span>
          </div>
        </div>
      )}

      {/* Category Filter + Items Table */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          {(["all", "ai", "voice"] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={cn(
                "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                category === cat
                  ? "bg-gray-900 text-white"
                  : "bg-white text-gray-600 border border-gray-300 hover:bg-gray-50"
              )}
            >
              {cat === "all" ? "All" : cat === "ai" ? "AI" : "Voice"}
            </button>
          ))}
          <span className="text-sm text-gray-500 ml-2">
            {total.toLocaleString()} item{total !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-400 animate-pulse">
              Loading cost data...
            </div>
          ) : items.length === 0 ? (
            <div className="p-8 text-center text-gray-400">
              No cost items for this period
            </div>
          ) : (
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                <tr>
                  <th className="px-4 py-3 text-left">Time</th>
                  <th className="px-4 py-3 text-left">Category</th>
                  <th className="px-4 py-3 text-left">Description</th>
                  <th className="px-4 py-3 text-left">Lead</th>
                  <th className="px-4 py-3 text-right">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {formatDateTime(item.timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                          item.category === "ai"
                            ? "bg-indigo-100 text-indigo-800"
                            : "bg-green-100 text-green-800"
                        )}
                      >
                        {item.category === "ai" ? "AI" : "Voice"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-gray-900">{item.description}</div>
                      <div className="text-xs text-gray-500">{item.detail}</div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {item.lead_id ? `#${item.lead_id}` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-gray-900">
                      {formatCostUsd(item.cost_usd)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Pagination footer */}
          {!loading && total > 0 && (
            <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 flex items-center justify-between text-sm">
              <span className="text-gray-500">
                Showing {page * 50 + 1}–{Math.min((page + 1) * 50, total)} of{" "}
                {total.toLocaleString()}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="rounded border border-gray-300 bg-white px-3 py-1 text-gray-700 hover:bg-gray-50 disabled:opacity-40"
                >
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasMore}
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
