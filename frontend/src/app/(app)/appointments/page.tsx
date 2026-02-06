"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatDateTime, statusColor } from "@/lib/utils";

interface Appointment {
  id: number;
  lead_id: number;
  rep_id: number;
  rep_name: string | null;
  status: string;
  scheduled_start: string;
  scheduled_end: string;
  address: string | null;
  notes: string | null;
}

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getAppointments()
      .then(setAppointments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="overflow-x-auto rounded-xl bg-white shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">ID</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Lead</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Rep</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Scheduled</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Address</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Notes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  Loading...
                </td>
              </tr>
            ) : appointments.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  No appointments found
                </td>
              </tr>
            ) : (
              appointments.map((appt) => (
                <tr key={appt.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">#{appt.id}</td>
                  <td className="px-4 py-3 text-sm">
                    <a
                      href={`/leads/${appt.lead_id}`}
                      className="text-solar-600 hover:text-solar-800"
                    >
                      Lead #{appt.lead_id}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {appt.rep_name || `Rep #${appt.rep_id}`}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor(appt.status)}`}>
                      {appt.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {formatDateTime(appt.scheduled_start)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {appt.address || "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                    {appt.notes || "—"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
