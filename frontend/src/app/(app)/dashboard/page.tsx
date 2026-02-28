"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Insights {
  narrative: string;
  key_drivers: string[];
  recommendations: string[];
}

interface KPIs {
  total_leads: number;
  hot_leads: number;
  warm_leads: number;
  cool_leads: number;
  appointments_scheduled: number;
  appointments_completed: number;
  total_outreach_attempts: number;
  avg_score: number | null;
  conversion_rate: number;
  status_breakdown: Record<string, number>;
}

const kpiCards = [
  { key: "total_leads", label: "Total Leads", color: "bg-blue-500" },
  { key: "hot_leads", label: "Hot Leads", color: "bg-red-500" },
  { key: "warm_leads", label: "Warm Leads", color: "bg-orange-500" },
  { key: "cool_leads", label: "Cool Leads", color: "bg-cyan-500" },
  { key: "appointments_scheduled", label: "Appointments", color: "bg-green-500" },
  { key: "total_outreach_attempts", label: "Outreach Attempts", color: "bg-purple-500" },
] as const;

export default function DashboardPage() {
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getKPIs().then(setKpis).catch((e) => setError(e.message));
    api.getInsights().then(setInsights).catch(() => {}); // Non-critical
  }, []);

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
        Failed to load dashboard: {error}
      </div>
    );
  }

  if (!kpis) {
    return <div className="animate-pulse text-gray-400">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {kpiCards.map(({ key, label, color }) => (
          <div
            key={key}
            className="rounded-xl bg-white p-6 shadow-sm border border-gray-200"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">{label}</p>
                <p className="mt-1 text-3xl font-bold text-gray-900">
                  {kpis[key as keyof KPIs] as number}
                </p>
              </div>
              <div className={cn("h-12 w-12 rounded-lg flex items-center justify-center", color)}>
                <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Avg Score */}
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Average Lead Score</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-bold text-gray-900">
              {kpis.avg_score ?? "—"}
            </span>
            <span className="text-sm text-gray-500">/ 100</span>
          </div>
          <div className="mt-3 h-2 w-full rounded-full bg-gray-200">
            <div
              className="h-2 rounded-full bg-solar-500 transition-all"
              style={{ width: `${kpis.avg_score ?? 0}%` }}
            />
          </div>
        </div>

        {/* Conversion Rate */}
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-500">Conversion Rate</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-4xl font-bold text-gray-900">
              {kpis.conversion_rate}%
            </span>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Leads reaching appointment stage
          </p>
        </div>
      </div>

      {/* Status Breakdown */}
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Status Breakdown</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {Object.entries(kpis.status_breakdown).map(([status, count]) => (
            <div
              key={status}
              className="rounded-lg bg-gray-50 p-3 text-center"
            >
              <p className="text-xs font-medium text-gray-500 uppercase">
                {status.replace(/_/g, " ")}
              </p>
              <p className="mt-1 text-xl font-bold text-gray-900">{count}</p>
            </div>
          ))}
        </div>
      </div>

      {/* AI Insights Panel */}
      {insights && (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900">AI Insights</h3>
          </div>
          <p className="text-sm text-gray-700 leading-relaxed mb-4">{insights.narrative}</p>
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {insights.key_drivers.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Drivers</h4>
                <ul className="space-y-1">
                  {insights.key_drivers.map((d, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-blue-500" />
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {insights.recommendations.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {insights.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-green-500" />
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
