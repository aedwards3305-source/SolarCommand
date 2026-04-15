"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn, formatDateTime, formatDate } from "@/lib/utils";

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

const STATUS_OPTIONS = [
  { value: "scheduled", label: "Scheduled", color: "bg-blue-100 text-blue-700" },
  { value: "confirmed", label: "Confirmed", color: "bg-green-100 text-green-700" },
  { value: "completed", label: "Completed", color: "bg-emerald-100 text-emerald-700" },
  { value: "no_show", label: "No Show", color: "bg-red-100 text-red-700" },
  { value: "cancelled", label: "Cancelled", color: "bg-gray-100 text-gray-500" },
  { value: "rescheduled", label: "Rescheduled", color: "bg-yellow-100 text-yellow-700" },
];

function statusBadge(status: string) {
  return STATUS_OPTIONS.find((s) => s.value === status)?.color || "bg-gray-100 text-gray-700";
}

export default function AppointmentsPage() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState<string>("all");

  // Edit modal state
  const [editing, setEditing] = useState<Appointment | null>(null);
  const [editStart, setEditStart] = useState("");
  const [editEnd, setEditEnd] = useState("");
  const [editNotes, setEditNotes] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  // Create modal state
  const [creating, setCreating] = useState(false);
  const [newLeadId, setNewLeadId] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newStart, setNewStart] = useState("");
  const [newEnd, setNewEnd] = useState("");
  const [newNotes, setNewNotes] = useState("");
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState("");

  // Lead search state
  const [leadSearchResults, setLeadSearchResults] = useState<Array<{
    id: number;
    first_name: string | null;
    last_name: string | null;
    phone: string | null;
    status: string;
  }>>([]);
  const [searchingLeads, setSearchingLeads] = useState(false);
  const [showLeadDropdown, setShowLeadDropdown] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    api
      .getAppointments()
      .then(setAppointments)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = filter === "all"
    ? appointments
    : appointments.filter((a) => a.status === filter);

  // ── Edit handlers ──
  function openEdit(appt: Appointment) {
    setEditing(appt);
    setEditStart(toLocalDatetime(appt.scheduled_start));
    setEditEnd(toLocalDatetime(appt.scheduled_end));
    setEditNotes(appt.notes || "");
    setEditStatus(appt.status);
    setEditError("");
  }

  async function saveEdit() {
    if (!editing) return;
    setEditSaving(true);
    setEditError("");
    try {
      await api.updateAppointment(editing.id, {
        scheduled_start: new Date(editStart).toISOString(),
        scheduled_end: new Date(editEnd).toISOString(),
        notes: editNotes,
        status: editStatus,
      });
      setEditing(null);
      load();
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Failed to update");
    } finally {
      setEditSaving(false);
    }
  }

  async function quickStatus(appt: Appointment, newStatus: string) {
    try {
      await api.updateAppointment(appt.id, { status: newStatus });
      load();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to update status");
    }
  }

  // ── Lead search ──
  // Hits the backend `q` param so we search the full lead table, not just
  // the 10 most-recent. Client-side filtering was causing "phantom save"
  // bugs: if the lead wasn't in the top 10 the dropdown stayed empty, the
  // Create button silently stayed disabled, and the rep thought they'd
  // saved an appointment that never posted.
  async function searchLeads(query: string) {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setLeadSearchResults([]);
      setShowLeadDropdown(false);
      return;
    }
    setSearchingLeads(true);
    try {
      const res = await api.getLeads({ q: trimmed, page_size: "20" });
      setLeadSearchResults(res.leads);
      setShowLeadDropdown(true);
    } catch {
      setLeadSearchResults([]);
    } finally {
      setSearchingLeads(false);
    }
  }

  function selectLead(lead: { id: number; first_name: string | null; last_name: string | null; phone: string | null }) {
    setNewLeadId(lead.id);
    setNewName(`${lead.first_name || ""} ${lead.last_name || ""}`.trim());
    setNewPhone(lead.phone || "");
    setShowLeadDropdown(false);
  }

  // ── Create handler ──
  async function handleCreate() {
    if (!user || !newLeadId) return;
    setCreateSaving(true);
    setCreateError("");
    try {
      await api.createAppointment({
        lead_id: newLeadId,
        rep_id: user.id,
        scheduled_start: new Date(newStart).toISOString(),
        scheduled_end: new Date(newEnd).toISOString(),
        notes: newNotes || undefined,
      });
      setCreating(false);
      setNewLeadId(null);
      setNewName("");
      setNewPhone("");
      setNewEmail("");
      setNewStart("");
      setNewEnd("");
      setNewNotes("");
      load();
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : "Failed to create");
    } finally {
      setCreateSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Appointments</h1>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Refresh
          </button>
          <button
            onClick={() => { setCreating(true); setCreateError(""); }}
            className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 transition-colors"
          >
            + New Appointment
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-1 flex-wrap">
        <FilterBtn label="All" value="all" current={filter} count={appointments.length} onClick={setFilter} />
        {STATUS_OPTIONS.map((s) => {
          const cnt = appointments.filter((a) => a.status === s.value).length;
          if (cnt === 0) return null;
          return (
            <FilterBtn key={s.value} label={s.label} value={s.value} current={filter} count={cnt} onClick={setFilter} />
          );
        })}
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl bg-white shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">When</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Lead</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Rep</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Address</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Notes</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading...</td>
              </tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">No appointments found</td>
              </tr>
            ) : (
              filtered.map((appt) => (
                <tr key={appt.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-gray-900">
                      {formatDateTime(appt.scheduled_start)}
                    </p>
                    <p className="text-xs text-gray-400">
                      to {new Date(appt.scheduled_end).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
                    </p>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <Link href={`/leads/${appt.lead_id}`} className="text-solar-600 hover:underline">
                      Lead #{appt.lead_id}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{appt.rep_name || `Rep #${appt.rep_id}`}</td>
                  <td className="px-4 py-3">
                    <span className={cn("inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium", statusBadge(appt.status))}>
                      {appt.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-[160px] truncate">{appt.address || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 max-w-[160px] truncate">{appt.notes || "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      <button
                        onClick={() => openEdit(appt)}
                        className="rounded px-2 py-1 text-xs font-medium text-solar-600 hover:bg-solar-50 transition-colors"
                      >
                        Edit
                      </button>
                      {appt.status === "scheduled" && (
                        <button
                          onClick={() => quickStatus(appt, "confirmed")}
                          className="rounded px-2 py-1 text-xs font-medium text-green-600 hover:bg-green-50 transition-colors"
                        >
                          Confirm
                        </button>
                      )}
                      {(appt.status === "scheduled" || appt.status === "confirmed") && (
                        <>
                          <button
                            onClick={() => quickStatus(appt, "completed")}
                            className="rounded px-2 py-1 text-xs font-medium text-emerald-600 hover:bg-emerald-50 transition-colors"
                          >
                            Complete
                          </button>
                          <button
                            onClick={() => quickStatus(appt, "no_show")}
                            className="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
                          >
                            No Show
                          </button>
                          <button
                            onClick={() => quickStatus(appt, "cancelled")}
                            className="rounded px-2 py-1 text-xs font-medium text-gray-500 hover:bg-gray-100 transition-colors"
                          >
                            Cancel
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Edit Modal ── */}
      {editing && (
        <Modal title={`Edit Appointment #${editing.id}`} onClose={() => setEditing(null)}>
          {editError && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-sm text-red-700 mb-3">
              {editError}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start</label>
                <input
                  type="datetime-local"
                  value={editStart}
                  onChange={(e) => setEditStart(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End</label>
                <input
                  type="datetime-local"
                  value={editEnd}
                  onChange={(e) => setEditEnd(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                rows={3}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setEditing(null)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                disabled={editSaving}
                className={cn(
                  "rounded-lg px-4 py-2 text-sm font-medium text-white",
                  editSaving ? "bg-gray-400" : "bg-solar-600 hover:bg-solar-700"
                )}
              >
                {editSaving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* ── Create Modal ── */}
      {creating && (
        <Modal title="New Appointment" onClose={() => setCreating(false)}>
          {createError && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-sm text-red-700 mb-3">
              {createError}
            </div>
          )}
          <div className="space-y-4">
            <div className="relative">
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => {
                  setNewName(e.target.value);
                  setNewLeadId(null);
                  searchLeads(e.target.value);
                }}
                onFocus={() => { if (leadSearchResults.length > 0) setShowLeadDropdown(true); }}
                onBlur={() => { setTimeout(() => setShowLeadDropdown(false), 200); }}
                placeholder="Search by name or phone"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
              {searchingLeads && (
                <div className="absolute right-3 top-8 text-xs text-gray-400">Searching...</div>
              )}
              {showLeadDropdown && (
                <div className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg max-h-48 overflow-y-auto">
                  {leadSearchResults.length > 0 ? (
                    leadSearchResults.map((lead) => (
                      <button
                        key={lead.id}
                        type="button"
                        onClick={() => selectLead(lead)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0"
                      >
                        <span className="font-medium">{lead.first_name} {lead.last_name}</span>
                        {lead.phone && <span className="ml-2 text-gray-500">{lead.phone}</span>}
                        <span className="ml-2 text-xs text-gray-400">#{lead.id}</span>
                      </button>
                    ))
                  ) : (
                    <div className="px-3 py-2 text-sm text-gray-400">
                      No matching lead — create the lead first, then book the appointment.
                    </div>
                  )}
                </div>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
              <input
                type="tel"
                value={newPhone}
                onChange={(e) => {
                  setNewPhone(e.target.value);
                  if (!newName) {
                    setNewLeadId(null);
                    searchLeads(e.target.value);
                  }
                }}
                placeholder="Phone number"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                readOnly={!!newLeadId}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="Email address"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                readOnly={!!newLeadId}
              />
            </div>
            {newLeadId && (
              <div className="rounded-lg bg-green-50 border border-green-200 px-3 py-2 text-sm text-green-700">
                Linked to Lead #{newLeadId}
              </div>
            )}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Start</label>
                <input
                  type="datetime-local"
                  value={newStart}
                  onChange={(e) => setNewStart(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">End</label>
                <input
                  type="datetime-local"
                  value={newEnd}
                  onChange={(e) => setNewEnd(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={newNotes}
                onChange={(e) => setNewNotes(e.target.value)}
                rows={3}
                placeholder="Optional notes"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            {(!newLeadId || !newStart || !newEnd) && (
              <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
                {!newLeadId
                  ? "Pick a lead from the dropdown before saving — typing a name alone won't link the appointment."
                  : "Start and end times are required."}
              </div>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setCreating(false)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={createSaving || !newLeadId || !newStart || !newEnd}
                className={cn(
                  "rounded-lg px-4 py-2 text-sm font-medium text-white",
                  createSaving || !newLeadId || !newStart || !newEnd ? "bg-gray-400 cursor-not-allowed" : "bg-solar-600 hover:bg-solar-700"
                )}
              >
                {createSaving ? "Creating..." : "Create Appointment"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

/* ── Helper components ─────────────────────────────────────────────────── */

function FilterBtn({
  label,
  value,
  current,
  count,
  onClick,
}: {
  label: string;
  value: string;
  current: string;
  count: number;
  onClick: (v: string) => void;
}) {
  return (
    <button
      onClick={() => onClick(value)}
      className={cn(
        "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
        current === value
          ? "bg-solar-600 text-white"
          : "text-gray-500 bg-gray-100 hover:bg-gray-200"
      )}
    >
      {label} ({count})
    </button>
  );
}

function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function toLocalDatetime(iso: string): string {
  const d = new Date(iso);
  const offset = d.getTimezoneOffset();
  const local = new Date(d.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}
