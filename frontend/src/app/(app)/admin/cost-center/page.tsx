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
      {/* Month selector */}
      <div className="flex justify-end">
        <select
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="admin-select"
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
        <div className="admin-kpi border-l-gray-800">
          <p className="admin-kpi-label">Total Cost</p>
          <p className="admin-kpi-value">
            {summary ? formatCostUsd(summary.total_cost) : "—"}
          </p>
        </div>
        <div className="admin-kpi border-l-indigo-400">
          <p className="admin-kpi-label">AI Cost</p>
          <p className="admin-kpi-value text-indigo-600">
            {summary ? formatCostUsd(summary.ai_cost) : "—"}
          </p>
          <p className="admin-kpi-sub">
            {summary ? `${summary.ai_run_count.toLocaleString()} runs` : ""}
          </p>
        </div>
        <div className="admin-kpi border-l-emerald-400">
          <p className="admin-kpi-label">Voice Cost</p>
          <p className="admin-kpi-value text-emerald-600">
            {summary ? formatCostUsd(summary.voice_cost) : "—"}
          </p>
          <p className="admin-kpi-sub">
            {summary ? `${summary.voice_call_count.toLocaleString()} calls` : ""}
          </p>
        </div>
        <div className="admin-kpi border-l-sunburst-400">
          <p className="admin-kpi-label">Transactions</p>
          <p className="admin-kpi-value">
            {summary
              ? (summary.ai_run_count + summary.voice_call_count).toLocaleString()
              : "—"}
          </p>
        </div>
      </div>

      {/* Daily Spending Chart */}
      {summary && summary.daily_totals.length > 0 && (
        <div className="admin-card p-6">
          <h3 className="admin-kpi-label mb-4">Daily Spending</h3>
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
                  <div
                    className="absolute bottom-0 left-0 right-0 flex flex-col rounded-t-sm overflow-hidden"
                    style={{ height: `${barH}px` }}
                  >
                    {aiH > 0 && (
                      <div
                        className="w-full bg-indigo-400/80"
                        style={{ height: `${aiH}px` }}
                      />
                    )}
                    {voiceH > 0 && (
                      <div
                        className="w-full bg-emerald-400/80"
                        style={{ height: `${voiceH}px` }}
                      />
                    )}
                  </div>
                  {dayTotal > 0 && (
                    <div className="absolute -top-7 left-1/2 -translate-x-1/2 hidden group-hover:block bg-gray-900 text-white text-[10px] px-2 py-1 rounded-md whitespace-nowrap z-10 pointer-events-none shadow-lg">
                      {formatCostUsd(dayTotal)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-2 text-[10px] text-gray-400">
            <span>{summary.daily_totals[0]?.date.slice(5)}</span>
            <span>{summary.daily_totals[summary.daily_totals.length - 1]?.date.slice(5)}</span>
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-indigo-400" />
              AI
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Voice
            </span>
          </div>
        </div>
      )}

      {/* Category Filter + Items Table */}
      <div className="space-y-4">
        <div className="admin-toolbar">
          {(["all", "ai", "voice"] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={category === cat ? "admin-btn-active" : "admin-btn"}
            >
              {cat === "all" ? "All" : cat === "ai" ? "AI" : "Voice"}
            </button>
          ))}
          <span className="ml-auto text-xs font-medium text-gray-400 tabular-nums">
            {total.toLocaleString()} item{total !== 1 ? "s" : ""}
          </span>
        </div>

        <div className="admin-card">
          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
              <p className="mt-3 text-sm text-gray-400">Loading cost data...</p>
            </div>
          ) : items.length === 0 ? (
            <div className="p-12 text-center text-gray-400 text-sm">
              No cost items for this period
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Category</th>
                    <th>Description</th>
                    <th>Lead</th>
                    <th className="text-right">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={item.id}>
                      <td className="text-gray-400 whitespace-nowrap text-xs tabular-nums">
                        {formatDateTime(item.timestamp)}
                      </td>
                      <td>
                        <span
                          className={cn(
                            "admin-badge",
                            item.category === "ai"
                              ? "bg-indigo-50 text-indigo-700"
                              : "bg-emerald-50 text-emerald-700"
                          )}
                        >
                          {item.category === "ai" ? "AI" : "Voice"}
                        </span>
                      </td>
                      <td>
                        <div className="text-gray-900 text-sm">{item.description}</div>
                        <div className="text-[11px] text-gray-400">{item.detail}</div>
                      </td>
                      <td className="text-gray-400 text-xs tabular-nums">
                        {item.lead_id ? `#${item.lead_id}` : "—"}
                      </td>
                      <td className="text-right font-mono text-sm tabular-nums text-gray-900">
                        {formatCostUsd(item.cost_usd)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {!loading && total > 0 && (
          <div className="admin-pagination">
            <span className="text-xs text-gray-400 tabular-nums">
              {page * 50 + 1}–{Math.min((page + 1) * 50, total)} of {total.toLocaleString()}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="admin-page-btn"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={!hasMore}
                className="admin-page-btn"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
