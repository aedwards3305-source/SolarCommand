"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cn, formatDateTime } from "@/lib/utils";

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
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="admin-card p-12 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
          <p className="mt-3 text-sm text-gray-400">Loading scripts...</p>
        </div>
      ) : scripts.length === 0 ? (
        <div className="admin-card p-12 text-center text-gray-400 text-sm">No scripts found</div>
      ) : (
        <div className="space-y-3">
          {scripts.map((s) => (
            <div key={s.id} className="admin-card">
              <button
                onClick={() => setExpanded(expanded === s.id ? null : s.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-50/70 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold text-gray-900">
                    {s.version_label}
                  </span>
                  <span className="admin-badge bg-solar-50 text-solar-700">
                    {s.channel}
                  </span>
                  {s.is_active && (
                    <span className="admin-badge bg-emerald-50 text-emerald-700">
                      Active
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-gray-400">
                    {formatDateTime(s.created_at)}
                  </span>
                  <svg
                    className={cn(
                      "h-4 w-4 text-gray-300 transition-transform",
                      expanded === s.id && "rotate-180"
                    )}
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
                <div className="border-t border-gray-100 bg-gray-50/50">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono p-5 leading-relaxed">
                    {s.content || "No content"}
                  </pre>
                  <div className="border-t border-gray-100 px-5 py-3">
                    <span className="text-[11px] text-gray-400">
                      Created by {s.created_by || "unknown"}
                    </span>
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
