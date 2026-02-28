"use client";

import { useEffect, useState, useCallback } from "react";
import { cn, formatDate } from "@/lib/utils";
import { leadgenApi } from "@/lib/api/leadgen";
import type { SourceHealthEntry } from "@/lib/types/leadgen";

function uptimeColor(pct: number): string {
  if (pct >= 99) return "text-green-700";
  if (pct >= 95) return "text-yellow-700";
  return "text-red-700";
}

function latencyColor(ms: number): string {
  if (ms <= 1000) return "text-green-700";
  if (ms <= 3000) return "text-yellow-700";
  return "text-red-700";
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

  // Summary metrics
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Source Health</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor data source uptime, ingestion volumes, and errors
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Avg Uptime</p>
          <p className={cn("mt-1 text-3xl font-bold", uptimeColor(avgUptime))}>
            {avgUptime.toFixed(1)}%
          </p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Sources Monitored</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{entries.length}</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Records Added (7d)</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{totalRecords7d.toLocaleString()}</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Error Sources</p>
          <p className={cn("mt-1 text-3xl font-bold", errorSources.length > 0 ? "text-red-600" : "text-green-700")}>
            {errorSources.length}
          </p>
        </div>
      </div>

      {/* Source Health Cards */}
      {loading ? (
        <div className="animate-pulse text-gray-400 p-8 text-center">Loading health data...</div>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => {
            const hasError = entry.last_sync_status === "error";
            return (
              <div
                key={entry.source_id}
                className={cn(
                  "rounded-xl bg-white p-6 shadow-sm border",
                  hasError ? "border-red-200" : "border-gray-200"
                )}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{entry.name}</h3>
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
                        {entry.source_type.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                      hasError
                        ? "bg-red-100 text-red-800"
                        : "bg-green-100 text-green-800"
                    )}
                  >
                    {hasError ? "Error" : "Healthy"}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-5">
                  <div>
                    <p className="text-xs text-gray-500">Uptime</p>
                    <p className={cn("text-lg font-bold", uptimeColor(entry.uptime_pct))}>
                      {entry.uptime_pct.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Avg Latency</p>
                    <p className={cn("text-lg font-bold", latencyColor(entry.avg_latency_ms))}>
                      {entry.avg_latency_ms < 1000
                        ? `${entry.avg_latency_ms}ms`
                        : `${(entry.avg_latency_ms / 1000).toFixed(1)}s`}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Added (7d)</p>
                    <p className="text-lg font-bold text-gray-900">
                      {entry.records_added_7d.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Updated (7d)</p>
                    <p className="text-lg font-bold text-gray-900">
                      {entry.records_updated_7d.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Last Sync</p>
                    <p className="text-sm font-medium text-gray-700">
                      {entry.last_sync_at ? formatDate(entry.last_sync_at) : "Never"}
                    </p>
                  </div>
                </div>

                {/* 7-day ingestion sparkline */}
                <div className="mt-4">
                  <p className="text-xs text-gray-500 mb-2">7-Day Ingestion Volume</p>
                  <div className="flex items-end gap-1 h-12">
                    {entry.last_7d_ingests.map((count, i) => {
                      const height = maxIngest7d > 0 ? (count / maxIngest7d) * 100 : 0;
                      return (
                        <div
                          key={i}
                          className="flex-1 group relative"
                        >
                          <div
                            className={cn(
                              "w-full rounded-t transition-all",
                              count === 0 ? "bg-red-300" : hasError && i >= 5 ? "bg-yellow-400" : "bg-solar-400"
                            )}
                            style={{ height: `${Math.max(height, 4)}%` }}
                          />
                          <div className="absolute -top-6 left-1/2 -translate-x-1/2 hidden group-hover:block bg-gray-900 text-white text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap">
                            {count.toLocaleString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-[10px] text-gray-400">7d ago</span>
                    <span className="text-[10px] text-gray-400">Today</span>
                  </div>
                </div>

                {/* Error detail */}
                {hasError && entry.last_error && (
                  <div className="mt-3 rounded-lg bg-red-50 border border-red-200 p-3">
                    <p className="text-xs font-medium text-red-800">Last Error</p>
                    <p className="text-sm text-red-700 mt-0.5">{entry.last_error}</p>
                    {entry.last_error_at && (
                      <p className="text-xs text-red-500 mt-1">{formatDate(entry.last_error_at)}</p>
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
