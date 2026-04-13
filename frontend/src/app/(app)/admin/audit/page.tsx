"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";

interface AuditEntry {
  id: number;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export default function AuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [page, setPage] = useState(1);
  const [entityFilter, setEntityFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchLog = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(page), page_size: "50" };
      if (entityFilter) params.entity_type = entityFilter;
      const data = await api.getAuditLog(params);
      setEntries(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  }, [page, entityFilter]);

  useEffect(() => {
    fetchLog();
  }, [fetchLog]);

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="admin-toolbar">
        <select
          value={entityFilter}
          onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}
          className="admin-select"
        >
          <option value="">All Entities</option>
          <option value="lead">Lead</option>
          <option value="appointment">Appointment</option>
          <option value="outreach_attempt">Outreach</option>
          <option value="consent_log">Consent</option>
        </select>
        <span className="ml-auto text-xs font-medium text-gray-400">
          Page {page}
        </span>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="admin-card">
        <div className="overflow-x-auto">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Old Value</th>
                <th>New Value</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center">
                    <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
                    <p className="mt-3 text-sm text-gray-400">Loading...</p>
                  </td>
                </tr>
              ) : entries.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400 text-sm">
                    No audit entries
                  </td>
                </tr>
              ) : (
                entries.map((e) => (
                  <tr key={e.id}>
                    <td className="text-xs text-gray-400 whitespace-nowrap tabular-nums">
                      {formatDateTime(e.created_at)}
                    </td>
                    <td className="text-sm text-gray-600">{e.actor}</td>
                    <td className="text-sm font-medium text-gray-900">{e.action}</td>
                    <td className="text-sm text-gray-600">
                      <span className="admin-badge bg-gray-50 text-gray-600">
                        {e.entity_type}
                        {e.entity_id != null && ` #${e.entity_id}`}
                      </span>
                    </td>
                    <td className="text-xs text-gray-400 max-w-[200px] truncate font-mono">
                      {e.old_value || "—"}
                    </td>
                    <td className="text-xs text-gray-400 max-w-[200px] truncate font-mono">
                      {e.new_value || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="admin-pagination">
        <span className="text-xs text-gray-400">Page {page}</span>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="admin-page-btn"
          >
            Previous
          </button>
          <button
            onClick={() => setPage(page + 1)}
            disabled={entries.length < 50}
            className="admin-page-btn"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
