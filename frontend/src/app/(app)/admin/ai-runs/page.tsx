"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatDateTime, cn } from "@/lib/utils";

interface AIRun {
  id: number;
  task_type: string;
  lead_id: number | null;
  conversation_id: number | null;
  model: string;
  temperature: number | null;
  prompt_version: string | null;
  tokens_in: number;
  tokens_out: number;
  cost_usd: number | null;
  latency_ms: number | null;
  status: string;
  error: string | null;
  created_at: string;
}

interface AIStats {
  total_runs_today: number;
  errors_today: number;
  avg_latency_ms: number;
  total_cost_today: number;
  runs_by_task: Record<string, number>;
}

const taskTypeColors: Record<string, string> = {
  sms_classification: "bg-blue-50 text-blue-700 ring-blue-600/10",
  qa_review: "bg-emerald-50 text-emerald-700 ring-emerald-600/10",
  objection_tags: "bg-amber-50 text-amber-700 ring-amber-600/10",
  nba: "bg-violet-50 text-violet-700 ring-violet-600/10",
  rep_brief: "bg-indigo-50 text-indigo-700 ring-indigo-600/10",
  script_suggest: "bg-pink-50 text-pink-700 ring-pink-600/10",
  weekly_insights: "bg-cyan-50 text-cyan-700 ring-cyan-600/10",
  memory_update: "bg-gray-50 text-gray-700 ring-gray-600/10",
};

const kpiAccents = {
  runs: "border-l-solar-500",
  errors: "border-l-red-400",
  latency: "border-l-amber-400",
  cost: "border-l-emerald-400",
};

export default function AIRunsPage() {
  const [runs, setRuns] = useState<AIRun[]>([]);
  const [stats, setStats] = useState<AIStats | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [expanded, setExpanded] = useState<number | null>(null);
  const [detail, setDetail] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (filter) params.task_type = filter;
    if (statusFilter) params.status = statusFilter;

    Promise.all([api.getAIRuns(params), api.getAIStats()])
      .then(([runsData, statsData]) => {
        setRuns(runsData.runs);
        setTotal(runsData.total);
        setStats(statsData);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [filter, statusFilter]);

  async function handleExpand(runId: number) {
    if (expanded === runId) {
      setExpanded(null);
      setDetail(null);
      return;
    }
    try {
      const d = await api.getAIRunDetail(runId);
      setDetail(d);
      setExpanded(runId);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div className={cn("admin-kpi", kpiAccents.runs)}>
            <p className="admin-kpi-label">Runs Today</p>
            <p className="admin-kpi-value">{stats.total_runs_today}</p>
          </div>
          <div className={cn("admin-kpi", kpiAccents.errors)}>
            <p className="admin-kpi-label">Errors</p>
            <p className={cn("admin-kpi-value", stats.errors_today > 0 ? "text-red-600" : "text-emerald-600")}>
              {stats.errors_today}
            </p>
          </div>
          <div className={cn("admin-kpi", kpiAccents.latency)}>
            <p className="admin-kpi-label">Avg Latency</p>
            <p className="admin-kpi-value">{stats.avg_latency_ms}<span className="text-sm font-normal text-gray-400 ml-0.5">ms</span></p>
          </div>
          <div className={cn("admin-kpi", kpiAccents.cost)}>
            <p className="admin-kpi-label">Cost Today</p>
            <p className="admin-kpi-value">${stats.total_cost_today.toFixed(4)}</p>
          </div>
        </div>
      )}

      {/* Task breakdown pills */}
      {stats && Object.keys(stats.runs_by_task).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.runs_by_task).map(([task, count]) => (
            <span
              key={task}
              className={cn(
                "admin-badge ring-1 ring-inset",
                taskTypeColors[task] || "bg-gray-50 text-gray-700 ring-gray-600/10"
              )}
            >
              {task.replace(/_/g, " ")}: {count}
            </span>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="admin-toolbar">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="admin-select"
        >
          <option value="">All task types</option>
          <option value="sms_classification">SMS Classification</option>
          <option value="qa_review">QA Review</option>
          <option value="objection_tags">Objection Tags</option>
          <option value="nba">NBA</option>
          <option value="rep_brief">Rep Brief</option>
          <option value="script_suggest">Script Suggest</option>
          <option value="weekly_insights">Weekly Insights</option>
          <option value="memory_update">Memory Update</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="admin-select"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
          <option value="pending">Pending</option>
        </select>
        <span className="ml-auto text-xs font-medium text-gray-400 tabular-nums">
          {total} total runs
        </span>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="admin-card p-12 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
          <p className="mt-3 text-sm text-gray-400">Loading AI runs...</p>
        </div>
      ) : runs.length === 0 ? (
        <div className="admin-card p-12 text-center text-gray-400 text-sm">
          No AI runs found
        </div>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <div key={run.id} className="admin-card">
              <button
                onClick={() => handleExpand(run.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50/70 transition-colors text-left"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="text-[11px] font-mono text-gray-300 tabular-nums">#{run.id}</span>
                  <span
                    className={cn(
                      "admin-badge ring-1 ring-inset",
                      taskTypeColors[run.task_type] || "bg-gray-50 text-gray-700 ring-gray-600/10"
                    )}
                  >
                    {run.task_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-xs text-gray-500 truncate">{run.model}</span>
                  {run.lead_id && (
                    <span className="text-[11px] text-gray-400">Lead #{run.lead_id}</span>
                  )}
                </div>
                <div className="flex items-center gap-4 flex-shrink-0">
                  {run.latency_ms != null && (
                    <span className="text-[11px] tabular-nums text-gray-400">{run.latency_ms}ms</span>
                  )}
                  <span className="text-[11px] tabular-nums text-gray-400">
                    {run.tokens_in + run.tokens_out} tok
                  </span>
                  {run.cost_usd != null && run.cost_usd > 0 && (
                    <span className="text-[11px] tabular-nums text-gray-400">${run.cost_usd.toFixed(4)}</span>
                  )}
                  <span
                    className={cn(
                      "admin-badge",
                      run.status === "success"
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-red-50 text-red-700"
                    )}
                  >
                    {run.status}
                  </span>
                  <span className="text-[11px] text-gray-400">{formatDateTime(run.created_at)}</span>
                  <svg
                    className={cn("h-4 w-4 text-gray-300 transition-transform", expanded === run.id && "rotate-180")}
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>
              {expanded === run.id && detail && (
                <div className="border-t border-gray-100 p-5 bg-gray-50/50">
                  <div className="grid grid-cols-2 gap-4 text-sm mb-4 lg:grid-cols-4">
                    <div>
                      <span className="admin-kpi-label">Model</span>
                      <p className="mt-0.5 font-medium text-gray-900">{String((detail as Record<string, unknown>).model)}</p>
                    </div>
                    <div>
                      <span className="admin-kpi-label">Temperature</span>
                      <p className="mt-0.5 font-medium text-gray-900">{String((detail as Record<string, unknown>).temperature)}</p>
                    </div>
                    <div>
                      <span className="admin-kpi-label">Prompt Version</span>
                      <p className="mt-0.5 font-medium text-gray-900">{String((detail as Record<string, unknown>).prompt_version)}</p>
                    </div>
                    <div>
                      <span className="admin-kpi-label">Tokens</span>
                      <p className="mt-0.5 font-medium text-gray-900 tabular-nums">
                        {String((detail as Record<string, unknown>).tokens_in)} in / {String((detail as Record<string, unknown>).tokens_out)} out
                      </p>
                    </div>
                  </div>
                  {!!(detail as Record<string, unknown>).error && (
                    <div className="mb-4 rounded-lg bg-red-50 border border-red-100 p-3 text-sm text-red-700">
                      {String((detail as Record<string, unknown>).error)}
                    </div>
                  )}
                  <div>
                    <p className="admin-kpi-label mb-2">Output JSON</p>
                    <pre className="whitespace-pre-wrap text-xs text-gray-600 font-mono bg-white rounded-lg p-4 border border-gray-100 max-h-64 overflow-y-auto leading-relaxed">
                      {JSON.stringify((detail as Record<string, unknown>).output_json, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
