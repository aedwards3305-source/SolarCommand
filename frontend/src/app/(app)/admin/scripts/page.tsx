"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

interface Script {
  id: number;
  version_label: string;
  channel: string;
  content: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
}

export default function ScriptsPage() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    api
      .getScripts()
      .then(setScripts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Call Scripts</h1>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading scripts...</div>
      ) : scripts.length === 0 ? (
        <div className="text-gray-400">No scripts found</div>
      ) : (
        <div className="space-y-4">
          {scripts.map((s) => (
            <div
              key={s.id}
              className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden"
            >
              <button
                onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-gray-900">
                    {s.version_label}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                    {s.channel}
                  </span>
                  {s.is_active && (
                    <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                      Active
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">
                    {formatDateTime(s.created_at)}
                  </span>
                  <svg
                    className={`h-4 w-4 text-gray-400 transition-transform ${expanded === s.id ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>
              {expanded === s.id && (
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                    {s.content || "No content"}
                  </pre>
                  <div className="mt-3 text-xs text-gray-500">
                    Created by: {s.created_by || "unknown"}
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
