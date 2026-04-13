"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cn, formatDateTime } from "@/lib/utils";

interface Experiment {
  id: number;
  name: string;
  channel: string;
  control_sends: number;
  variant_sends: number;
  control_responses: number;
  variant_responses: number;
  control_conversions: number;
  variant_conversions: number;
  is_active: boolean;
  started_at: string;
  control_response_rate: number;
  variant_response_rate: number;
  control_conversion_rate: number;
  variant_conversion_rate: number;
}

function MetricCell({
  value,
  label,
  highlight,
}: {
  value: string;
  label: string;
  highlight?: boolean;
}) {
  return (
    <div className="text-center">
      <p className={cn("text-xl font-bold tabular-nums", highlight ? "text-emerald-600" : "text-gray-900")}>
        {value}
      </p>
      <p className="text-[11px] text-gray-400 mt-0.5">{label}</p>
    </div>
  );
}

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getExperiments()
      .then(setExperiments)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <div className="admin-card p-12 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
          <p className="mt-3 text-sm text-gray-400">Loading experiments...</p>
        </div>
      ) : experiments.length === 0 ? (
        <div className="admin-card p-12 text-center">
          <svg className="mx-auto h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          <p className="mt-3 text-sm text-gray-500">No experiments yet</p>
          <p className="text-xs text-gray-400 mt-1">Create script variants and start A/B testing to see results here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {experiments.map((exp) => (
            <div key={exp.id} className="admin-card p-6">
              {/* Experiment header */}
              <div className="flex items-center justify-between mb-5">
                <div>
                  <h3 className="text-base font-semibold text-gray-900">{exp.name}</h3>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="admin-badge bg-solar-50 text-solar-700">
                      {exp.channel}
                    </span>
                    <span
                      className={cn(
                        "admin-badge",
                        exp.is_active
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-gray-100 text-gray-500"
                      )}
                    >
                      {exp.is_active ? "Active" : "Ended"}
                    </span>
                    <span className="text-[11px] text-gray-400">
                      Started {formatDateTime(exp.started_at)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Control vs Variant comparison */}
              <div className="grid grid-cols-2 gap-4">
                {/* Control */}
                <div className="rounded-lg border border-gray-100 bg-gray-50/50 p-4">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="h-2 w-2 rounded-full bg-gray-400" />
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">Control (A)</h4>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <MetricCell
                      value={exp.control_sends.toLocaleString()}
                      label="Sends"
                    />
                    <MetricCell
                      value={`${exp.control_response_rate.toFixed(1)}%`}
                      label="Response"
                    />
                    <MetricCell
                      value={`${exp.control_conversion_rate.toFixed(1)}%`}
                      label="Conversion"
                    />
                  </div>
                </div>

                {/* Variant */}
                <div className="rounded-lg border border-solar-100 bg-solar-50/30 p-4">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="h-2 w-2 rounded-full bg-solar-500" />
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-solar-600">Variant (B)</h4>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <MetricCell
                      value={exp.variant_sends.toLocaleString()}
                      label="Sends"
                    />
                    <MetricCell
                      value={`${exp.variant_response_rate.toFixed(1)}%`}
                      label="Response"
                      highlight={exp.variant_response_rate > exp.control_response_rate}
                    />
                    <MetricCell
                      value={`${exp.variant_conversion_rate.toFixed(1)}%`}
                      label="Conversion"
                      highlight={exp.variant_conversion_rate > exp.control_conversion_rate}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
