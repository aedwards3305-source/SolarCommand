"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, Deal } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn, formatDate, formatCurrency } from "@/lib/utils";

/* ── Constants ─────────────────────────────────────────────────────────── */

const DEAL_STATUSES = [
  { value: "pending_contract", label: "Pending Contract", color: "bg-yellow-100 text-yellow-700" },
  { value: "contract_signed", label: "Contract Signed", color: "bg-blue-100 text-blue-700" },
  { value: "permit_submitted", label: "Permit Submitted", color: "bg-indigo-100 text-indigo-700" },
  { value: "scheduled_install", label: "Scheduled Install", color: "bg-purple-100 text-purple-700" },
  { value: "installed", label: "Installed", color: "bg-emerald-100 text-emerald-700" },
  { value: "pto_granted", label: "PTO Granted", color: "bg-green-100 text-green-800" },
  { value: "cancelled", label: "Cancelled", color: "bg-red-100 text-red-600" },
];

const FINANCING_TYPES = [
  { value: "cash", label: "Cash" },
  { value: "loan", label: "Loan" },
  { value: "lease", label: "Lease" },
  { value: "ppa", label: "PPA" },
  { value: "other", label: "Other" },
];

function dealStatusBadge(status: string) {
  return DEAL_STATUSES.find((s) => s.value === status)?.color || "bg-gray-100 text-gray-700";
}

function dealStatusLabel(status: string) {
  return DEAL_STATUSES.find((s) => s.value === status)?.label || status.replace(/_/g, " ");
}

/* ── Summary Interface ─────────────────────────────────────────────────── */

interface DealsSummary {
  total_deals: number;
  total_revenue: number;
  total_commission: number;
  avg_deal_value: number;
  total_kw_sold: number;
  deals_by_status: Record<string, number>;
  deals_by_financing: Record<string, number>;
}

/* ── Main Page ─────────────────────────────────────────────────────────── */

export default function SalesLogPage() {
  const { user } = useAuth();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [summary, setSummary] = useState<DealsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [mineOnly, setMineOnly] = useState(false);

  // Create modal
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({
    lead_id: "",
    contract_value: "",
    system_size_kw: "",
    financing_type: "cash",
    commission_amount: "",
    adders_total: "",
    panel_count: "",
    panel_brand: "",
    inverter_type: "",
    battery_included: false,
    annual_production_kwh: "",
    sale_date: new Date().toISOString().slice(0, 10),
    install_date: "",
    notes: "",
  });
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState("");

  // Edit modal
  const [editing, setEditing] = useState<Deal | null>(null);
  const [editForm, setEditForm] = useState<Record<string, string | boolean>>({});
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    const params: Record<string, string> = {};
    if (mineOnly) params.mine_only = "true";
    if (filter !== "all") params.status_filter = filter;
    api.getDeals(params).then(setDeals).catch((e) => setError(e.message)).finally(() => setLoading(false));
    api.getDealsSummary(mineOnly).then(setSummary).catch(() => {});
  }, [mineOnly, filter]);

  useEffect(() => { load(); }, [load]);

  // ── Create ──
  function resetForm() {
    setForm({
      lead_id: "", contract_value: "", system_size_kw: "", financing_type: "cash",
      commission_amount: "", adders_total: "", panel_count: "", panel_brand: "",
      inverter_type: "", battery_included: false, annual_production_kwh: "",
      sale_date: new Date().toISOString().slice(0, 10), install_date: "", notes: "",
    });
  }

  async function handleCreate() {
    setCreateSaving(true);
    setCreateError("");
    try {
      await api.createDeal({
        lead_id: parseInt(form.lead_id),
        contract_value: parseFloat(form.contract_value),
        system_size_kw: parseFloat(form.system_size_kw),
        financing_type: form.financing_type,
        commission_amount: form.commission_amount ? parseFloat(form.commission_amount) : undefined,
        adders_total: form.adders_total ? parseFloat(form.adders_total) : undefined,
        panel_count: form.panel_count ? parseInt(form.panel_count) : undefined,
        panel_brand: form.panel_brand || undefined,
        inverter_type: form.inverter_type || undefined,
        battery_included: form.battery_included,
        annual_production_kwh: form.annual_production_kwh ? parseFloat(form.annual_production_kwh) : undefined,
        sale_date: new Date(form.sale_date).toISOString(),
        install_date: form.install_date ? new Date(form.install_date).toISOString() : undefined,
        notes: form.notes || undefined,
      });
      setCreating(false);
      resetForm();
      load();
    } catch (e: unknown) {
      setCreateError(e instanceof Error ? e.message : "Failed to create deal");
    } finally {
      setCreateSaving(false);
    }
  }

  // ── Edit ──
  function openEdit(deal: Deal) {
    setEditing(deal);
    setEditForm({
      status: deal.status,
      contract_value: String(deal.contract_value),
      system_size_kw: String(deal.system_size_kw),
      financing_type: deal.financing_type,
      commission_amount: deal.commission_amount != null ? String(deal.commission_amount) : "",
      adders_total: deal.adders_total != null ? String(deal.adders_total) : "",
      panel_count: deal.panel_count != null ? String(deal.panel_count) : "",
      panel_brand: deal.panel_brand || "",
      inverter_type: deal.inverter_type || "",
      battery_included: deal.battery_included,
      install_date: deal.install_date ? deal.install_date.slice(0, 10) : "",
      pto_date: deal.pto_date ? deal.pto_date.slice(0, 10) : "",
      notes: deal.notes || "",
    });
    setEditError("");
  }

  async function handleEdit() {
    if (!editing) return;
    setEditSaving(true);
    setEditError("");
    try {
      const data: Record<string, unknown> = {};
      if (editForm.status !== editing.status) data.status = editForm.status;
      if (editForm.contract_value !== String(editing.contract_value)) data.contract_value = parseFloat(editForm.contract_value as string);
      if (editForm.system_size_kw !== String(editing.system_size_kw)) data.system_size_kw = parseFloat(editForm.system_size_kw as string);
      if (editForm.financing_type !== editing.financing_type) data.financing_type = editForm.financing_type;
      if (editForm.commission_amount) data.commission_amount = parseFloat(editForm.commission_amount as string);
      if (editForm.adders_total) data.adders_total = parseFloat(editForm.adders_total as string);
      if (editForm.panel_count) data.panel_count = parseInt(editForm.panel_count as string);
      if (editForm.panel_brand) data.panel_brand = editForm.panel_brand;
      if (editForm.inverter_type) data.inverter_type = editForm.inverter_type;
      data.battery_included = editForm.battery_included;
      if (editForm.install_date) data.install_date = new Date(editForm.install_date as string).toISOString();
      if (editForm.pto_date) data.pto_date = new Date(editForm.pto_date as string).toISOString();
      if (editForm.notes !== (editing.notes || "")) data.notes = editForm.notes;

      await api.updateDeal(editing.id, data);
      setEditing(null);
      load();
    } catch (e: unknown) {
      setEditError(e instanceof Error ? e.message : "Failed to update deal");
    } finally {
      setEditSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sales Log</h1>
          <p className="text-sm text-gray-500 mt-1">Track closed deals, commissions, and install progress.</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMineOnly(!mineOnly)}
            className={cn(
              "rounded-lg px-3 py-2 text-sm font-medium transition-colors border",
              mineOnly ? "bg-solar-50 border-solar-300 text-solar-700" : "border-gray-300 text-gray-600 hover:bg-gray-50"
            )}
          >
            {mineOnly ? "My Deals" : "All Deals"}
          </button>
          <button
            onClick={() => { setCreating(true); setCreateError(""); }}
            className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 transition-colors"
          >
            + Record Sale
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          <SummaryCard label="Total Deals" value={summary.total_deals} />
          <SummaryCard label="Total Revenue" value={formatCurrency(summary.total_revenue)} color="text-emerald-600" />
          <SummaryCard label="Total Commission" value={formatCurrency(summary.total_commission)} color="text-green-600" />
          <SummaryCard label="Avg Deal Value" value={formatCurrency(summary.avg_deal_value)} />
          <SummaryCard label="kW Sold" value={`${summary.total_kw_sold} kW`} color="text-solar-600" />
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-1 flex-wrap">
        <FilterBtn label="All" value="all" current={filter} onClick={setFilter} />
        {DEAL_STATUSES.map((s) => (
          <FilterBtn key={s.value} label={s.label} value={s.value} current={filter} onClick={setFilter} />
        ))}
      </div>

      {/* Deals Table */}
      <div className="overflow-x-auto rounded-xl bg-white shadow-sm border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Customer</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Sale Date</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Contract</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">System</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Financing</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Rep</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
            ) : deals.length === 0 ? (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-gray-400">No deals found. Record your first sale!</td></tr>
            ) : (
              deals.map((deal) => (
                <tr key={deal.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/leads/${deal.lead_id}`} className="text-sm font-medium text-solar-600 hover:underline">
                      {deal.customer_name}
                    </Link>
                    {deal.customer_address && (
                      <p className="text-xs text-gray-400 truncate max-w-[180px]">{deal.customer_address}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{formatDate(deal.sale_date)}</td>
                  <td className="px-4 py-3">
                    <p className="text-sm font-semibold text-gray-900">{formatCurrency(deal.contract_value)}</p>
                    {deal.commission_amount != null && (
                      <p className="text-xs text-green-600">Comm: {formatCurrency(deal.commission_amount)}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm text-gray-900">{deal.system_size_kw} kW</p>
                    {deal.panel_count && <p className="text-xs text-gray-400">{deal.panel_count} panels</p>}
                    {deal.battery_included && <p className="text-xs text-purple-500">+ Battery</p>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 capitalize">{deal.financing_type}</td>
                  <td className="px-4 py-3">
                    <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", dealStatusBadge(deal.status))}>
                      {dealStatusLabel(deal.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{deal.rep_name || `Rep #${deal.rep_id}`}</td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => openEdit(deal)}
                      className="rounded px-2 py-1 text-xs font-medium text-solar-600 hover:bg-solar-50 transition-colors"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* ── Create Modal ── */}
      {creating && (
        <Modal title="Record New Sale" onClose={() => setCreating(false)}>
          {createError && <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-sm text-red-700 mb-3">{createError}</div>}
          <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Lead ID *" value={form.lead_id} onChange={(v) => setForm({ ...form, lead_id: v })} type="number" placeholder="Lead ID" />
              <FormField label="Sale Date *" value={form.sale_date} onChange={(v) => setForm({ ...form, sale_date: v })} type="date" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Contract Value ($) *" value={form.contract_value} onChange={(v) => setForm({ ...form, contract_value: v })} type="number" placeholder="e.g. 35000" />
              <FormField label="System Size (kW) *" value={form.system_size_kw} onChange={(v) => setForm({ ...form, system_size_kw: v })} type="number" placeholder="e.g. 8.5" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Financing</label>
                <select value={form.financing_type} onChange={(e) => setForm({ ...form, financing_type: e.target.value })} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  {FINANCING_TYPES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>
              <FormField label="Commission ($)" value={form.commission_amount} onChange={(v) => setForm({ ...form, commission_amount: v })} type="number" placeholder="Optional" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <FormField label="Panel Count" value={form.panel_count} onChange={(v) => setForm({ ...form, panel_count: v })} type="number" placeholder="e.g. 20" />
              <FormField label="Panel Brand" value={form.panel_brand} onChange={(v) => setForm({ ...form, panel_brand: v })} placeholder="e.g. REC" />
              <FormField label="Inverter" value={form.inverter_type} onChange={(v) => setForm({ ...form, inverter_type: v })} placeholder="e.g. Enphase" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Adders ($)" value={form.adders_total} onChange={(v) => setForm({ ...form, adders_total: v })} type="number" placeholder="Battery, critter guard..." />
              <FormField label="Annual Production (kWh)" value={form.annual_production_kwh} onChange={(v) => setForm({ ...form, annual_production_kwh: v })} type="number" placeholder="e.g. 12000" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Install Date" value={form.install_date} onChange={(v) => setForm({ ...form, install_date: v })} type="date" />
              <div className="flex items-end pb-1">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form.battery_included} onChange={(e) => setForm({ ...form, battery_included: e.target.checked })} className="rounded border-gray-300 text-solar-600 focus:ring-solar-500" />
                  <span className="text-sm font-medium text-gray-700">Battery Included</span>
                </label>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="Optional notes" />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-gray-100 mt-4">
            <button onClick={() => setCreating(false)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50">Cancel</button>
            <button
              onClick={handleCreate}
              disabled={createSaving || !form.lead_id || !form.contract_value || !form.system_size_kw}
              className={cn("rounded-lg px-4 py-2 text-sm font-medium text-white", createSaving || !form.lead_id || !form.contract_value || !form.system_size_kw ? "bg-gray-400" : "bg-solar-600 hover:bg-solar-700")}
            >
              {createSaving ? "Recording..." : "Record Sale"}
            </button>
          </div>
        </Modal>
      )}

      {/* ── Edit Modal ── */}
      {editing && (
        <Modal title={`Edit Deal #${editing.id} — ${editing.customer_name}`} onClose={() => setEditing(null)}>
          {editError && <div className="rounded-lg bg-red-50 border border-red-200 p-2 text-sm text-red-700 mb-3">{editError}</div>}
          <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Deal Status</label>
              <select
                value={editForm.status as string}
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                {DEAL_STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Contract Value ($)" value={editForm.contract_value as string} onChange={(v) => setEditForm({ ...editForm, contract_value: v })} type="number" />
              <FormField label="System Size (kW)" value={editForm.system_size_kw as string} onChange={(v) => setEditForm({ ...editForm, system_size_kw: v })} type="number" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Financing</label>
                <select value={editForm.financing_type as string} onChange={(e) => setEditForm({ ...editForm, financing_type: e.target.value })} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm">
                  {FINANCING_TYPES.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </div>
              <FormField label="Commission ($)" value={editForm.commission_amount as string} onChange={(v) => setEditForm({ ...editForm, commission_amount: v })} type="number" />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <FormField label="Panel Count" value={editForm.panel_count as string} onChange={(v) => setEditForm({ ...editForm, panel_count: v })} type="number" />
              <FormField label="Panel Brand" value={editForm.panel_brand as string} onChange={(v) => setEditForm({ ...editForm, panel_brand: v })} />
              <FormField label="Inverter" value={editForm.inverter_type as string} onChange={(v) => setEditForm({ ...editForm, inverter_type: v })} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Install Date" value={editForm.install_date as string} onChange={(v) => setEditForm({ ...editForm, install_date: v })} type="date" />
              <FormField label="PTO Date" value={editForm.pto_date as string} onChange={(v) => setEditForm({ ...editForm, pto_date: v })} type="date" />
            </div>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={editForm.battery_included as boolean} onChange={(e) => setEditForm({ ...editForm, battery_included: e.target.checked })} className="rounded border-gray-300 text-solar-600 focus:ring-solar-500" />
                <span className="text-sm font-medium text-gray-700">Battery Included</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea value={editForm.notes as string} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })} rows={2} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t border-gray-100 mt-4">
            <button onClick={() => setEditing(null)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50">Cancel</button>
            <button
              onClick={handleEdit}
              disabled={editSaving}
              className={cn("rounded-lg px-4 py-2 text-sm font-medium text-white", editSaving ? "bg-gray-400" : "bg-solar-600 hover:bg-solar-700")}
            >
              {editSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

/* ── Sub-components ────────────────────────────────────────────────────── */

function SummaryCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className={cn("mt-1 text-xl font-bold", color || "text-gray-900")}>{value}</p>
    </div>
  );
}

function FilterBtn({ label, value, current, onClick }: { label: string; value: string; current: string; onClick: (v: string) => void }) {
  return (
    <button
      onClick={() => onClick(value)}
      className={cn(
        "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
        current === value ? "bg-solar-600 text-white" : "text-gray-500 bg-gray-100 hover:bg-gray-200"
      )}
    >
      {label}
    </button>
  );
}

function FormField({ label, value, onChange, type = "text", placeholder }: {
  label: string; value: string; onChange: (v: string) => void; type?: string; placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-solar-500 focus:ring-1 focus:ring-solar-500 outline-none"
      />
    </div>
  );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-xl rounded-xl bg-white p-6 shadow-xl">
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
