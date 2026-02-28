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
  if (!status) return { label: "Never synced", cls: "bg-gray-100 text-gray-600" };
  if (status === "success") return { label: "Healthy", cls: "bg-green-100 text-green-800" };
  if (status === "error") return { label: "Error", cls: "bg-red-100 text-red-800" };
  return { label: status, cls: "bg-yellow-100 text-yellow-800" };
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Sources</h1>
          <p className="mt-1 text-sm text-gray-500">
            Configure and monitor lead discovery data sources
          </p>
        </div>
        <button
          onClick={() => setShowWizard(true)}
          className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700"
        >
          + Add Source
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>
      )}

      {syncMsg && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">{syncMsg}</div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Active Sources</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{activeCount}</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Total Records</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{totalRecords.toLocaleString()}</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500">Sources with Errors</p>
          <p className={cn("mt-1 text-3xl font-bold", errorCount > 0 ? "text-red-600" : "text-gray-900")}>
            {errorCount}
          </p>
        </div>
      </div>

      {/* Source Cards */}
      {loading ? (
        <div className="animate-pulse text-gray-400 p-8 text-center">Loading sources...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {sources.map((source) => {
            const badge = statusBadge(source.last_sync_status);
            return (
              <div key={source.id} className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{source.name}</h3>
                    <div className="mt-1 flex items-center gap-2">
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
                        {SOURCE_TYPE_LABELS[source.source_type] || source.source_type}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700">
                        {LICENSE_LABELS[source.license] || source.license}
                      </span>
                      {source.ingestion_cadence && (
                        <span className="text-xs text-gray-500">{source.ingestion_cadence}</span>
                      )}
                    </div>
                  </div>
                  <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", badge.cls)}>
                    {badge.label}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">Records Synced</span>
                    <p className="font-medium">{source.records_synced.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Last Sync</span>
                    <p className="font-medium">
                      {source.last_sync_at ? formatDate(source.last_sync_at) : "Never"}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Connector</span>
                    <p className="font-medium text-xs text-gray-600 truncate" title={source.connector_class}>
                      {source.connector_class.split(".").pop()}
                    </p>
                  </div>
                  <div>
                    <span className="text-gray-500">Status</span>
                    <p className={cn("font-medium", source.is_active ? "text-green-600" : "text-gray-400")}>
                      {source.is_active ? "Active" : "Inactive"}
                    </p>
                  </div>
                </div>

                {source.license_detail && (
                  <p className="mt-2 text-xs text-gray-500 italic">{source.license_detail}</p>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    onClick={() => handleSync(source.id)}
                    disabled={syncingId === source.id}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    {syncingId === source.id ? "Syncing..." : "Sync Now"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Source Wizard Modal */}
      {showWizard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-labelledby="wizard-title">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h2 id="wizard-title" className="text-lg font-semibold text-gray-900">Add Data Source</h2>
              <button onClick={resetWizard} className="text-gray-400 hover:text-gray-600" aria-label="Close wizard">
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
                      "h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium",
                      wizardStep >= s
                        ? "bg-solar-600 text-white"
                        : "bg-gray-100 text-gray-400"
                    )}
                  >
                    {s}
                  </div>
                  {s < 3 && (
                    <div className={cn("h-0.5 w-8", wizardStep > s ? "bg-solar-600" : "bg-gray-200")} />
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
                        "rounded-lg border p-3 text-left text-sm",
                        wizardType === type
                          ? "border-solar-600 bg-solar-50 text-solar-700"
                          : "border-gray-200 text-gray-700 hover:bg-gray-50"
                      )}
                    >
                      {SOURCE_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => setWizardStep(2)}
                    disabled={!wizardType}
                    className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50"
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
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">License Type</label>
                  <select
                    value={wizardLicense}
                    onChange={(e) => setWizardLicense(e.target.value as LicenseType)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
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
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none"
                  >
                    <option value="hourly">Hourly</option>
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                  </select>
                </div>

                {wizardType === "byod_upload" && (
                  <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center">
                    <svg className="mx-auto h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                    <p className="mt-2 text-sm text-gray-600">Drop CSV file here or click to browse</p>
                    <p className="mt-1 text-xs text-gray-400">CSV must contain address_line1, city, state, zip_code columns</p>
                  </div>
                )}

                <div className="flex justify-between">
                  <button
                    onClick={() => setWizardStep(1)}
                    className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Back
                  </button>
                  <button
                    onClick={() => setWizardStep(3)}
                    disabled={!wizardName || !wizardLicense}
                    className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}

            {/* Step 3: Test & Confirm */}
            {wizardStep === 3 && (
              <div className="space-y-4">
                <div className="rounded-lg bg-gray-50 p-4 text-sm space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Type</span>
                    <span className="font-medium">{SOURCE_TYPE_LABELS[wizardType as SourceType] || wizardType}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Name</span>
                    <span className="font-medium">{wizardName}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">License</span>
                    <span className="font-medium">{LICENSE_LABELS[wizardLicense as LicenseType] || wizardLicense}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Cadence</span>
                    <span className="font-medium capitalize">{wizardCadence}</span>
                  </div>
                </div>

                <button
                  onClick={handleTestConnection}
                  disabled={testing}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  {testing ? "Testing..." : "Test Connection"}
                </button>

                {testResult && (
                  <div
                    className={cn(
                      "rounded-lg p-3 text-sm",
                      testResult.success
                        ? "bg-green-50 border border-green-200 text-green-700"
                        : "bg-red-50 border border-red-200 text-red-700"
                    )}
                  >
                    {testResult.message}
                    {testResult.record_count != null && (
                      <span className="block mt-1 text-xs">
                        {testResult.record_count.toLocaleString()} records available
                      </span>
                    )}
                  </div>
                )}

                <div className="flex justify-between">
                  <button
                    onClick={() => setWizardStep(2)}
                    className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Back
                  </button>
                  <button
                    onClick={resetWizard}
                    className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700"
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
