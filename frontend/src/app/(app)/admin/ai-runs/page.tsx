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
  sms_classification: "bg-blue-100 text-blue-800",
  qa_review: "bg-green-100 text-green-800",
  objection_tags: "bg-amber-100 text-amber-800",
  nba: "bg-purple-100 text-purple-800",
  rep_brief: "bg-indigo-100 text-indigo-800",
  script_suggest: "bg-pink-100 text-pink-800",
  weekly_insights: "bg-cyan-100 text-cyan-800",
  memory_update: "bg-gray-100 text-gray-800",
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

    Promise.all([
      api.getAIRuns(params),
      api.getAIStats(),
    ])
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
      <h1 className="text-2xl font-bold text-gray-900">AI Operator Runs</h1>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
            <p className="text-sm text-gray-500">Runs Today</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_runs_today}</p>
          </div>
          <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
            <p className="text-sm text-gray-500">Errors</p>
            <p className={cn("text-2xl font-bold", stats.errors_today > 0 ? "text-red-600" : "text-green-600")}>
              {stats.errors_today}
            </p>
          </div>
          <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
            <p className="text-sm text-gray-500">Avg Latency</p>
            <p className="text-2xl font-bold text-gray-900">{stats.avg_latency_ms}ms</p>
          </div>
          <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
            <p className="text-sm text-gray-500">Cost Today</p>
            <p className="text-2xl font-bold text-gray-900">${stats.total_cost_today.toFixed(4)}</p>
          </div>
        </div>
      )}

      {/* Task breakdown */}
      {stats && Object.keys(stats.runs_by_task).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(stats.runs_by_task).map(([task, count]) => (
            <span
              key={task}
              className={cn("inline-flex items-center rounded-full px-3 py-1 text-xs font-medium", taskTypeColors[task] || "bg-gray-100 text-gray-800")}
            >
              {task}: {count}
            </span>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
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
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
          <option value="pending">Pending</option>
        </select>
        <span className="self-center text-sm text-gray-500">{total} total runs</span>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading AI runs...</div>
      ) : runs.length === 0 ? (
        <div className="text-gray-400">No AI runs found</div>
      ) : (
        <div className="space-y-2">
          {runs.map((run) => (
            <div key={run.id} className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden">
              <button
                onClick={() => handleExpand(run.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors text-left"
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="text-xs font-mono text-gray-400">#{run.id}</span>
                  <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", taskTypeColors[run.task_type] || "bg-gray-100 text-gray-800")}>
                    {run.task_type}
                  </span>
                  <span className="text-sm text-gray-600 truncate">
                    {run.model}
                  </span>
                  {run.lead_id && (
                    <span className="text-xs text-gray-500">Lead #{run.lead_id}</span>
                  )}
                </div>
                <div className="flex items-center gap-4 flex-shrink-0">
                  {run.latency_ms != null && (
                    <span className="text-xs text-gray-500">{run.latency_ms}ms</span>
                  )}
                  <span className="text-xs text-gray-500">
                    {run.tokens_in + run.tokens_out} tok
                  </span>
                  {run.cost_usd != null && run.cost_usd > 0 && (
                    <span className="text-xs text-gray-500">${run.cost_usd.toFixed(4)}</span>
                  )}
                  <span className={cn(
                    "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                    run.status === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  )}>
                    {run.status}
                  </span>
                  <span className="text-xs text-gray-500">{formatDateTime(run.created_at)}</span>
                </div>
              </button>
              {expanded === run.id && detail && (
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                  <div className="grid grid-cols-2 gap-4 text-sm mb-4">
                    <div>
                      <span className="text-gray-500">Model:</span>{" "}
                      <span className="font-medium">{(detail as Record<string, unknown>).model as string}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Temperature:</span>{" "}
                      <span className="font-medium">{String((detail as Record<string, unknown>).temperature)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Prompt Version:</span>{" "}
                      <span className="font-medium">{String((detail as Record<string, unknown>).prompt_version)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Tokens:</span>{" "}
                      <span className="font-medium">{String((detail as Record<string, unknown>).tokens_in)} in / {String((detail as Record<string, unknown>).tokens_out)} out</span>
                    </div>
                  </div>
                  {!!(detail as Record<string, unknown>).error && (
                    <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
                      {String((detail as Record<string, unknown>).error)}
                    </div>
                  )}
                  <div>
                    <p className="text-xs font-semibold text-gray-500 mb-1">Output JSON</p>
                    <pre className="whitespace-pre-wrap text-xs text-gray-700 font-mono bg-white rounded-lg p-3 border border-gray-200 max-h-64 overflow-y-auto">
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
