"use client";

import { useEffect, useState, useCallback } from "react";
import { cn, formatDate } from "@/lib/utils";
import { leadgenApi } from "@/lib/api/leadgen";
import type { SourceConfig, SourceType, LicenseType } from "@/lib/types/leadgen";

const SOURCE_TYPE_LABELS: Record<SourceType, string> = {
  tax_assessor: "Tax Assessor",
  building_permit: "Building Permit",
  utility_territory: "Utility Territory",
  solar_suitability: "Solar Suitability",
  demographic_band: "Demographic Band",
  mls: "MLS",
  contact_enrichment: "Contact Enrichment",
  byod_upload: "BYOD Upload",
  vendor_feed: "Vendor Feed",
};

const LICENSE_LABELS: Record<LicenseType, string> = {
  public_record: "Public Record",
  public_data: "Public Data",
  vendor_feed: "Vendor Feed",
  vendor_api: "Vendor API",
  org_declared: "Org Declared",
  mls_licensed: "MLS Licensed",
};

function statusBadge(status: string | null) {
  if (!status) return { label: "Never synced", cls: "bg-gray-50 text-gray-500" };
  if (status === "success") return { label: "Healthy", cls: "bg-emerald-50 text-emerald-700" };
  if (status === "error") return { label: "Error", cls: "bg-red-50 text-red-700" };
  return { label: status, cls: "bg-amber-50 text-amber-700" };
}

export default function DataSourcesPage() {
  const [sources, setSources] = useState<SourceConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [syncMsg, setSyncMsg] = useState("");
  const [showWizard, setShowWizard] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [wizardType, setWizardType] = useState<SourceType | "">("");
  const [wizardName, setWizardName] = useState("");
  const [wizardLicense, setWizardLicense] = useState<LicenseType | "">("");
  const [wizardCadence, setWizardCadence] = useState("weekly");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; record_count?: number } | null>(null);

  const fetchSources = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await leadgenApi.listSources();
      setSources(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  async function handleSync(id: string) {
    setSyncingId(id);
    setSyncMsg("");
    try {
      await leadgenApi.syncSource(id);
      setSyncMsg("Sync queued");
      fetchSources();
    } catch (e) {
      setSyncMsg(e instanceof Error ? e.message : "Sync failed");
    } finally {
      setSyncingId(null);
      setTimeout(() => setSyncMsg(""), 3000);
    }
  }

  async function handleTestConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await leadgenApi.testSourceConnection({
        source_type: wizardType,
        name: wizardName,
      });
      setTestResult(result);
    } catch (e) {
      setTestResult({ success: false, message: e instanceof Error ? e.message : "Test failed" });
    } finally {
      setTesting(false);
    }
  }

  function resetWizard() {
    setShowWizard(false);
    setWizardStep(1);
    setWizardType("");
    setWizardName("");
    setWizardLicense("");
    setWizardCadence("weekly");
    setTestResult(null);
  }

  const totalRecords = sources.reduce((acc, s) => acc + s.records_synced, 0);
  const activeCount = sources.filter((s) => s.is_active).length;
  const errorCount = sources.filter((s) => s.last_sync_status === "error").length;

  return (
    <div className="space-y-6">
      {/* Action bar */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowWizard(true)}
          className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-solar-700 transition-colors"
        >
          + Add Source
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {syncMsg && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-3 text-sm text-emerald-700">{syncMsg}</div>
      )}

      {/* Summary KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="admin-kpi border-l-solar-500">
          <p className="admin-kpi-label">Active Sources</p>
          <p className="admin-kpi-value">{activeCount}</p>
        </div>
        <div className="admin-kpi border-l-sunburst-400">
          <p className="admin-kpi-label">Total Records</p>
          <p className="admin-kpi-value">{totalRecords.toLocaleString()}</p>
        </div>
        <div className="admin-kpi border-l-red-400">
          <p className="admin-kpi-label">Sources with Errors</p>
          <p className={cn("admin-kpi-value", errorCount > 0 ? "text-red-500" : "text-gray-900")}>
            {errorCount}
          </p>
        </div>
      </div>

      {/* Source Cards */}
      {loading ? (
        <div className="admin-card p-12 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-solar-500" />
          <p className="mt-3 text-sm text-gray-400">Loading sources...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {sources.map((source) => {
            const badge = statusBadge(source.last_sync_status);
            return (
              <div key={source.id} className="admin-card p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{source.name}</h3>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className="admin-badge bg-gray-50 text-gray-500">
                        {SOURCE_TYPE_LABELS[source.source_type] || source.source_type}
                      </span>
                      <span className="admin-badge bg-solar-50 text-solar-600">
                        {LICENSE_LABELS[source.license] || source.license}
                      </span>
                      {source.ingestion_cadence && (
                        <span className="text-[11px] text-gray-400">{source.ingestion_cadence}</span>
                      )}
                    </div>
                  </div>
                  <span className={cn("admin-badge", badge.cls)}>
                    {badge.label}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="admin-kpi-label">Records Synced</span>
                    <p className="mt-0.5 font-medium tabular-nums">{source.records_synced.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="admin-kpi-label">Last Sync</span>
                    <p className="mt-0.5 font-medium">
                      {source.last_sync_at ? formatDate(source.last_sync_at) : "Never"}
                    </p>
                  </div>
                  <div>
                    <span className="admin-kpi-label">Connector</span>
                    <p className="mt-0.5 font-medium text-xs text-gray-600 truncate" title={source.connector_class}>
                      {source.connector_class.split(".").pop()}
                    </p>
                  </div>
                  <div>
                    <span className="admin-kpi-label">Status</span>
                    <p className={cn("mt-0.5 font-medium", source.is_active ? "text-emerald-600" : "text-gray-400")}>
                      {source.is_active ? "Active" : "Inactive"}
                    </p>
                  </div>
                </div>

                {source.license_detail && (
                  <p className="mt-3 text-[11px] text-gray-400 italic">{source.license_detail}</p>
                )}

                <div className="mt-4 pt-4 border-t border-gray-50">
                  <button
                    onClick={() => handleSync(source.id)}
                    disabled={syncingId === source.id}
                    className="admin-page-btn"
                  >
                    {syncingId === source.id ? (
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-gray-300 border-t-solar-500" />
                        Syncing...
                      </span>
                    ) : (
                      "Sync Now"
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Source Wizard Modal */}
      {showWizard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="wizard-title">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-gray-100">
            <div className="flex items-center justify-between mb-6">
              <h2 id="wizard-title" className="text-lg font-semibold text-gray-900">Add Data Source</h2>
              <button onClick={resetWizard} className="text-gray-400 hover:text-gray-600 transition-colors" aria-label="Close wizard">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Step indicators */}
            <div className="mb-6 flex items-center gap-2">
              {[1, 2, 3].map((s) => (
                <div key={s} className="flex items-center gap-2">
                  <div
                    className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium transition-colors",
                      wizardStep >= s
                        ? "bg-solar-600 text-white shadow-sm"
                        : "bg-gray-100 text-gray-400"
                    )}
                  >
                    {wizardStep > s ? (
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                      </svg>
                    ) : (
                      s
                    )}
                  </div>
                  {s < 3 && (
                    <div className={cn("h-0.5 w-8 rounded-full transition-colors", wizardStep > s ? "bg-solar-500" : "bg-gray-200")} />
                  )}
                </div>
              ))}
            </div>

            {/* Step 1: Type */}
            {wizardStep === 1 && (
              <div className="space-y-4">
                <label className="block text-sm font-medium text-gray-700">Source Type</label>
                <div className="grid grid-cols-2 gap-2">
                  {(Object.keys(SOURCE_TYPE_LABELS) as SourceType[]).map((type) => (
                    <button
                      key={type}
                      onClick={() => setWizardType(type)}
                      className={cn(
                        "rounded-lg border p-3 text-left text-sm transition-all",
                        wizardType === type
                          ? "border-solar-500 bg-solar-50 text-solar-700 shadow-sm"
                          : "border-gray-200 text-gray-700 hover:bg-gray-50 hover:border-gray-300"
                      )}
                    >
                      {SOURCE_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>
                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => setWizardStep(2)}
                    disabled={!wizardType}
                    className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 2: Config */}
            {wizardStep === 2 && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input
                    type="text"
                    value={wizardName}
                    onChange={(e) => setWizardName(e.target.value)}
                    placeholder="e.g., Baltimore County Tax Assessor"
                    className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm outline-none transition-colors focus:border-solar-400 focus:ring-2 focus:ring-solar-100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">License Type</label>
                  <select
                    value={wizardLicense}
                    onChange={(e) => setWizardLicense(e.target.value as LicenseType)}
                    className="admin-select w-full"
                  >
                    <option value="">Select license...</option>
                    {(Object.keys(LICENSE_LABELS) as LicenseType[]).map((lt) => (
                      <option key={lt} value={lt}>{LICENSE_LABELS[lt]}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ingestion Cadence</label>
                  <select
                    value={wizardCadence}
                    onChange={(e) => setWizardCadence(e.target.value)}
                    className="admin-select w-full"
                  >
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                  </select>
                </div>

                {wizardType === "byod_upload" && (
                  <div className="rounded-lg border-2 border-dashed border-gray-200 p-6 text-center transition-colors hover:border-solar-300 hover:bg-solar-50/30">
                    <svg className="mx-auto h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                    <p className="mt-2 text-sm text-gray-600">Drop CSV file here or click to browse</p>
                    <p className="mt-1 text-[11px] text-gray-400">CSV must contain address_line1, city, state, zip_code columns</p>
                  </div>
                )}

                <div className="flex justify-between pt-2">
                  <button onClick={() => setWizardStep(1)} className="admin-btn">
                    Back
                  </button>
                  <button
                    onClick={() => setWizardStep(3)}
                    disabled={!wizardName || !wizardLicense}
                    className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Test & Confirm */}
            {wizardStep === 3 && (
              <div className="space-y-4">
                <div className="rounded-lg bg-gray-50 border border-gray-100 p-4 text-sm space-y-2.5">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Type</span>
                    <span className="font-medium text-gray-900">{SOURCE_TYPE_LABELS[wizardType as SourceType] || wizardType}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Name</span>
                    <span className="font-medium text-gray-900">{wizardName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">License</span>
                    <span className="font-medium text-gray-900">{LICENSE_LABELS[wizardLicense as LicenseType] || wizardLicense}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Cadence</span>
                    <span className="font-medium text-gray-900 capitalize">{wizardCadence}</span>
                  </div>
                </div>

                <button
                  onClick={handleTestConnection}
                  disabled={testing}
                  className="admin-btn w-full justify-center"
                >
                  {testing ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-gray-300 border-t-solar-500" />
                      Testing...
                    </span>
                  ) : (
                    "Test Connection"
                  )}
                </button>

                {testResult && (
                  <div
                    className={cn(
                      "rounded-lg p-3 text-sm border",
                      testResult.success
                        ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                        : "bg-red-50 border-red-200 text-red-700"
                    )}
                  >
                    {testResult.message}
                    {testResult.record_count != null && (
                      <span className="block mt-1 text-xs tabular-nums">
                        {testResult.record_count.toLocaleString()} records available
                      </span>
                    )}
                  </div>
                )}

                <div className="flex justify-between pt-2">
                  <button onClick={() => setWizardStep(2)} className="admin-btn">
                    Back
                  </button>
                  <button
                    onClick={resetWizard}
                    className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 transition-colors"
                  >
                    Add Source
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
