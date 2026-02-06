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
      <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>

      <div className="flex gap-3">
        <select
          value={entityFilter}
          onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
        >
          <option value="">All Entities</option>
          <option value="lead">Lead</option>
          <option value="appointment">Appointment</option>
          <option value="outreach_attempt">Outreach</option>
          <option value="consent_log">Consent</option>
        </select>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Time</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actor</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Action</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Entity</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Old Value</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">New Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td>
              </tr>
            ) : entries.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400">No audit entries</td>
              </tr>
            ) : (
              entries.map((e) => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                    {formatDateTime(e.created_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{e.actor}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{e.action}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {e.entity_type}
                    {e.entity_id != null && ` #${e.entity_id}`}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">
                    {e.old_value || "—"}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">
                    {e.new_value || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={() => setPage(Math.max(1, page - 1))}
          disabled={page === 1}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
        >
          Previous
        </button>
        <span className="text-sm text-gray-500">Page {page}</span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={entries.length < 50}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
}
