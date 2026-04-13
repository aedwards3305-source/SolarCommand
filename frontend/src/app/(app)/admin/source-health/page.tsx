"use client";

import { useEffect, useState, useCallback } from "react";
import { cn, formatDate } from "@/lib/utils";
import { leadgenApi } from "@/lib/api/leadgen";
import type { SourceHealthEntry } from "@/lib/types/leadgen";

function uptimeColor(pct: number): string {
  if (pct >= 99) return "text-emerald-600";
  if (pct >= 95) return "text-amber-500";
  return "text-red-500";
}

function latencyColor(ms: number): string {
  if (ms <= 1000) return "text-emerald-600";
  if (ms <= 3000) return "text-amber-500";
  return "text-red-500";
}

export default function SourceHealthPage() {
  const [entries, setEntries] = useState<SourceHealthEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await leadgenApi.getSourceHealth();
      setEntries(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const avgUptime =
    entries.length > 0
      ? entries.reduce((sum, e) => sum + e.uptime_pct, 0) / entries.length
      : 0;
  const totalRecords7d = entries.reduce((sum, e) => sum + e.records_added_7d, 0);
  const errorSources = entries.filter((e) => e.last_sync_status === "error");
  const maxIngest7d = Math.max(
    ...entries.flatMap((e) => e.last_7d_ingests),
    1
  );

  return (
    <div className="space-y-6">
      {/* Action bar */}
      <div className="flex justify-end">
        <button
          onClick={fetchData}
          disabled={loading}
          className="admin-btn"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-gray-300 border-t-solar-500" />
              Refreshing...
            </span>
          ) : (
            "Refresh"
          )}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="admin-kpi border-l-emerald-400">
          <p className="admin-kpi-label">Avg Uptime</p>
          <p className={cn("admin-kpi-value", uptimeColor(avgUptime))}>
            {avgUptime.toFixed(1)}%
          </p>
        </div>
        <div className="admin-kpi border-l-solar-500">
          <p className="admin-kpi-label">Sources Monitored</p>
          <p className="admin-kpi-value">{entries.length}</p>
        </div>
        <div className="admin-kpi border-l-sunburst-400">
          <p className="admin-kpi-label">Records Added (7d)</p>
          <p className="admin-kpi-value">{totalRecords7d.toLocaleString()}</p>
        </div>
        <div className="admin-kpi border-l-red-400">
          <p className="admin-kpi-label">Error Sources</p>
          <p className={cn("admin-kpi-value", errorSources.length > 0 ? "text-red-500" : "text-emerald-600")}>
            {errorSources.length}
          </p>
        </div>
      </div>

      {/* Source Health Cards */}
      {loading ? (
        <div className="admin-card p-12 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
          <p className="mt-3 text-sm text-gray-400">Loading health data...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => {
            const hasError = entry.last_sync_status === "error";
            return (
              <div
                key={entry.source_id}
                className={cn(
                  "admin-card p-6",
                  hasError && "border-l-red-400"
                )}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{entry.name}</h3>
                      <span className="admin-badge bg-gray-50 text-gray-500">
                        {entry.source_type.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                  <span
                    className={cn(
                      "admin-badge",
                      hasError
                        ? "bg-red-50 text-red-700"
                        : "bg-emerald-50 text-emerald-700"
                    )}
                  >
                    {hasError ? "Error" : "Healthy"}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-5">
                  <div>
                    <p className="admin-kpi-label">Uptime</p>
                    <p className={cn("mt-0.5 text-lg font-bold tabular-nums", uptimeColor(entry.uptime_pct))}>
                      {entry.uptime_pct.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="admin-kpi-label">Avg Latency</p>
                    <p className={cn("mt-0.5 text-lg font-bold tabular-nums", latencyColor(entry.avg_latency_ms))}>
                      {entry.avg_latency_ms < 1000
                        ? `${entry.avg_latency_ms}ms`
                        : `${(entry.avg_latency_ms / 1000).toFixed(1)}s`}
                    </p>
                  </div>
                  <div>
                    <p className="admin-kpi-label">Added (7d)</p>
                    <p className="mt-0.5 text-lg font-bold text-gray-900 tabular-nums">
                      {entry.records_added_7d.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="admin-kpi-label">Updated (7d)</p>
                    <p className="mt-0.5 text-lg font-bold text-gray-900 tabular-nums">
                      {entry.records_updated_7d.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="admin-kpi-label">Last Sync</p>
                    <p className="mt-0.5 text-sm font-medium text-gray-600">
                      {entry.last_sync_at ? formatDate(entry.last_sync_at) : "Never"}
                    </p>
                  </div>
                </div>

                {/* 7-day ingestion sparkline */}
                <div className="mt-5">
                  <p className="admin-kpi-label mb-2">7-Day Ingestion Volume</p>
                  <div className="flex items-end gap-1 h-12">
                    {entry.last_7d_ingests.map((count, i) => {
                      const height = maxIngest7d > 0 ? (count / maxIngest7d) * 100 : 0;
                      return (
                        <div key={i} className="flex-1 group relative">
                          <div
                            className={cn(
                              "w-full rounded-t transition-all",
                              count === 0
                                ? "bg-red-200"
                                : hasError && i >= 5
                                ? "bg-amber-300"
                                : "bg-solar-400/70"
                            )}
                            style={{ height: `${Math.max(height, 4)}%` }}
                          />
                          <div className="absolute -top-7 left-1/2 -translate-x-1/2 hidden group-hover:block bg-gray-900 text-white text-[10px] px-2 py-1 rounded-md whitespace-nowrap shadow-lg">
                            {count.toLocaleString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-gray-300">7d ago</span>
                    <span className="text-[10px] text-gray-300">Today</span>
                  </div>
                </div>

                {/* Error detail */}
                {hasError && entry.last_error && (
                  <div className="mt-4 rounded-lg bg-red-50 border border-red-100 p-3">
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-red-400">Last Error</p>
                    <p className="text-sm text-red-700 mt-1">{entry.last_error}</p>
                    {entry.last_error_at && (
                      <p className="text-[11px] text-red-400 mt-1">{formatDate(entry.last_error_at)}</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
