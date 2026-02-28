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
      <h1 className="text-2xl font-bold text-gray-900">Script A/B Experiments</h1>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading experiments...</div>
      ) : experiments.length === 0 ? (
        <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center text-gray-400">
          No experiments yet. Create script variants and start A/B testing to see results here.
        </div>
      ) : (
        <div className="space-y-4">
          {experiments.map((exp) => (
            <div key={exp.id} className="rounded-xl bg-white shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{exp.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                      {exp.channel}
                    </span>
                    <span className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                      exp.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                    )}>
                      {exp.is_active ? "Active" : "Ended"}
                    </span>
                    <span className="text-xs text-gray-500">Started {formatDateTime(exp.started_at)}</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                {/* Control */}
                <div className="rounded-lg bg-gray-50 p-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">Control (A)</h4>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{exp.control_sends}</p>
                      <p className="text-xs text-gray-500">Sends</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{exp.control_response_rate.toFixed(1)}%</p>
                      <p className="text-xs text-gray-500">Response</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{exp.control_conversion_rate.toFixed(1)}%</p>
                      <p className="text-xs text-gray-500">Conversion</p>
                    </div>
                  </div>
                </div>

                {/* Variant */}
                <div className="rounded-lg bg-blue-50 p-4">
                  <h4 className="text-sm font-semibold text-blue-700 mb-3">Variant (B)</h4>
                  <div className="grid grid-cols-3 gap-3 text-center">
                    <div>
                      <p className="text-2xl font-bold text-gray-900">{exp.variant_sends}</p>
                      <p className="text-xs text-gray-500">Sends</p>
                    </div>
                    <div>
                      <p className={cn("text-2xl font-bold", exp.variant_response_rate > exp.control_response_rate ? "text-green-700" : "text-gray-900")}>
                        {exp.variant_response_rate.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500">Response</p>
                    </div>
                    <div>
                      <p className={cn("text-2xl font-bold", exp.variant_conversion_rate > exp.control_conversion_rate ? "text-green-700" : "text-gray-900")}>
                        {exp.variant_conversion_rate.toFixed(1)}%
                      </p>
                      <p className="text-xs text-gray-500">Conversion</p>
                    </div>
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
