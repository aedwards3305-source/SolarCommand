"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { cn, formatDate, formatCurrency } from "@/lib/utils";
import { leadgenApi } from "@/lib/api/leadgen";
import type { DiscoveredLead } from "@/lib/types/leadgen";

function discoveryStatusColor(status: string): string {
  const colors: Record<string, string> = {
    discovered: "bg-gray-100 text-gray-800",
    scoring: "bg-yellow-100 text-yellow-800",
    scored: "bg-purple-100 text-purple-800",
    enriching: "bg-blue-100 text-blue-800",
    enriched: "bg-blue-100 text-blue-800",
    activation_ready: "bg-green-100 text-green-800",
    activated: "bg-emerald-100 text-emerald-800",
    rejected: "bg-red-100 text-red-800",
    archived: "bg-gray-100 text-gray-500",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
}

function scoreBadge(score: number | null) {
  if (score == null) return { label: "—", cls: "bg-gray-100 text-gray-600" };
  if (score >= 75) return { label: `${score} Hot`, cls: "bg-red-100 text-red-800" };
  if (score >= 50) return { label: `${score} Warm`, cls: "bg-orange-100 text-orange-800" };
  return { label: `${score} Cool`, cls: "bg-blue-100 text-blue-800" };
}

export default function DiscoveredLeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const leadId = params.id as string;

  const [lead, setLead] = useState<DiscoveredLead | null>(null);
  const [error, setError] = useState("");
  const [enriching, setEnriching] = useState(false);
  const [activating, setActivating] = useState(false);
  const [enrichMsg, setEnrichMsg] = useState("");

  const fetchLead = useCallback(async () => {
    try {
      const data = await leadgenApi.getDiscoveredLead(leadId);
      setLead(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [leadId]);

  useEffect(() => {
    fetchLead();
  }, [fetchLead]);

  async function handleEnrich() {
    setEnriching(true);
    setEnrichMsg("");
    try {
      await leadgenApi.enrichDiscoveredLead(leadId);
      setEnrichMsg("Enrichment queued");
      setTimeout(() => {
        fetchLead();
        setEnrichMsg("");
      }, 3000);
    } catch (e: unknown) {
      setEnrichMsg(e instanceof Error ? e.message : "Enrichment failed");
    } finally {
      setEnriching(false);
    }
  }

  async function handleActivate() {
    if (!confirm("Activate this lead? It will be added to your outreach pipeline.")) return;
    setActivating(true);
    try {
      const res = await leadgenApi.activateDiscoveredLead(leadId);
      router.push(`/leads/${res.lead_id}`);
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Activation failed");
      setActivating(false);
    }
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
        {error}
      </div>
    );
  }

  if (!lead) {
    return <div className="animate-pulse text-gray-400">Loading discovered lead...</div>;
  }

  const ownerName =
    lead.property.owner_first_name || lead.property.owner_last_name
      ? `${lead.property.owner_first_name ?? ""} ${lead.property.owner_last_name ?? ""}`.trim()
      : null;

  const badge = scoreBadge(lead.discovery_score);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/discovery" className="text-sm text-gray-500 hover:text-gray-700">
            &larr; Back to Discovery
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-gray-900">
            {ownerName || "Unknown Owner"}
          </h1>
          <p className="text-sm text-gray-500">{lead.property.address_line1}</p>
          <div className="mt-2 flex items-center gap-3">
            <span
              className={cn(
                "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
                discoveryStatusColor(lead.status)
              )}
            >
              {lead.status.replace(/_/g, " ")}
            </span>
            <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", badge.cls)}>
              {badge.label}
            </span>
            <span className="text-xs text-gray-500">
              {lead.source_records.length} source{lead.source_records.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {enrichMsg && (
            <span className="text-sm text-green-700 bg-green-50 rounded-lg px-3 py-1.5">{enrichMsg}</span>
          )}
          <button
            onClick={handleEnrich}
            disabled={enriching}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            {enriching ? "Enriching..." : "Enrich"}
          </button>
          <button
            onClick={handleActivate}
            disabled={activating || lead.status === "activated"}
            className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 disabled:opacity-50"
          >
            {activating ? "Activating..." : "Activate →"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Property Details */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Property Details</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Address</span>
                <p className="font-medium">{lead.property.address_line1}</p>
                <p>{lead.property.city}, {lead.property.state} {lead.property.zip_code}</p>
              </div>
              <div>
                <span className="text-gray-500">County</span>
                <p className="font-medium">{lead.property.county ?? "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Parcel ID</span>
                <p className="font-medium">{lead.property.parcel_id ?? "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Type</span>
                <p className="font-medium">{lead.property.property_type?.replace(/_/g, " ") ?? "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Year Built</span>
                <p className="font-medium">{lead.property.year_built ?? "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Building SqFt</span>
                <p className="font-medium">
                  {lead.property.building_sqft ? lead.property.building_sqft.toLocaleString() : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Lot Size</span>
                <p className="font-medium">
                  {lead.property.lot_size_sqft ? `${lead.property.lot_size_sqft.toLocaleString()} sqft` : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Roof Area</span>
                <p className="font-medium">
                  {lead.property.roof_area_sqft ? `${lead.property.roof_area_sqft.toLocaleString()} sqft` : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Assessed Value</span>
                <p className="font-medium">{formatCurrency(lead.property.assessed_value)}</p>
              </div>
              <div>
                <span className="text-gray-500">Last Sale</span>
                <p className="font-medium">
                  {lead.property.last_sale_date ? formatDate(lead.property.last_sale_date) : "—"}
                  {lead.property.last_sale_price ? ` (${formatCurrency(lead.property.last_sale_price)})` : ""}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Owner Occupied</span>
                <p className={cn("font-medium", lead.property.owner_occupied ? "text-green-600" : "text-gray-600")}>
                  {lead.property.owner_occupied == null ? "—" : lead.property.owner_occupied ? "Yes" : "No"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Existing Solar</span>
                <p className={cn("font-medium", lead.property.has_existing_solar ? "text-red-600" : "text-green-600")}>
                  {lead.property.has_existing_solar ? "Yes" : "No"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Utility</span>
                <p className="font-medium">
                  {lead.property.utility_name ?? "—"}
                  {lead.property.utility_rate_zone ? ` (${lead.property.utility_rate_zone})` : ""}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Avg Rate</span>
                <p className="font-medium">
                  {lead.property.avg_rate_kwh ? `$${lead.property.avg_rate_kwh}/kWh` : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Tree Cover</span>
                <p className="font-medium">
                  {lead.property.tree_cover_pct != null ? `${lead.property.tree_cover_pct}%` : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Median Income</span>
                <p className="font-medium">{formatCurrency(lead.property.median_household_income)}</p>
              </div>
            </div>
          </div>

          {/* Permit History */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Permit History</h2>
            {lead.permits.length === 0 ? (
              <p className="text-sm text-gray-400">No permits found</p>
            ) : (
              <div className="space-y-3">
                {lead.permits.map((permit) => {
                  const isHighIntent = permit.category === "roof_replacement" || permit.category === "electrical_upgrade";
                  return (
                    <div
                      key={permit.id}
                      className={cn(
                        "rounded-lg p-4 border",
                        isHighIntent
                          ? "bg-amber-50 border-amber-200"
                          : "bg-gray-50 border-gray-200"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900">
                              {permit.category.replace(/_/g, " ")}
                            </span>
                            {isHighIntent && (
                              <span className="inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-800 uppercase">
                                High Intent Signal
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-gray-600">{permit.raw_description}</p>
                        </div>
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                            permit.status === "final"
                              ? "bg-green-100 text-green-800"
                              : "bg-blue-100 text-blue-800"
                          )}
                        >
                          {permit.status ?? "—"}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-4 text-xs text-gray-500">
                        <span>Permit # {permit.permit_number}</span>
                        <span>{permit.jurisdiction}</span>
                        {permit.issue_date && <span>Issued {formatDate(permit.issue_date)}</span>}
                        {permit.final_date && <span>Final {formatDate(permit.final_date)}</span>}
                        {permit.contractor_name && <span>{permit.contractor_name}</span>}
                        {permit.estimated_cost != null && (
                          <span>Est. {formatCurrency(permit.estimated_cost)}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Source Provenance */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Source Provenance</h2>
            <div className="space-y-3">
              {lead.source_records.map((src) => (
                <div key={src.id} className="rounded-lg bg-gray-50 border border-gray-200 p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">{src.dataset_name}</span>
                        <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
                          {src.source_type.replace(/_/g, " ")}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">
                        {src.retrieval_method.replace(/_/g, " ")} &middot; Retrieved{" "}
                        {formatDate(src.retrieval_timestamp)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-700">
                        {src.license.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-gray-500">
                        Q: {src.quality_score}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {Object.entries(src.evidence_fields).map(([field, value]) => (
                      <span
                        key={field}
                        className="inline-flex items-center rounded bg-white border border-gray-200 px-2 py-0.5 text-[10px] text-gray-600"
                      >
                        <span className="font-medium text-gray-700 mr-1">{field}:</span>
                        {String(value)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Discovery Score Breakdown */}
          {lead.score_breakdown && (
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-1">Discovery Score</h2>
              <p className="text-xs text-gray-500 mb-4">Model {lead.score_breakdown.model_version}</p>
              <div className="space-y-3">
                {[
                  { label: "Roof Suitability", score: lead.score_breakdown.roof_suitability, max: lead.score_breakdown.roof_suitability_max },
                  { label: "Ownership Signal", score: lead.score_breakdown.ownership_signal, max: lead.score_breakdown.ownership_signal_max },
                  { label: "Financial Capacity", score: lead.score_breakdown.financial_capacity, max: lead.score_breakdown.financial_capacity_max },
                  { label: "Utility Economics", score: lead.score_breakdown.utility_economics, max: lead.score_breakdown.utility_economics_max },
                  { label: "Solar Potential", score: lead.score_breakdown.solar_potential, max: lead.score_breakdown.solar_potential_max },
                  { label: "Permit Triggers", score: lead.score_breakdown.permit_triggers, max: lead.score_breakdown.permit_triggers_max },
                  { label: "Neighborhood", score: lead.score_breakdown.neighborhood_adoption, max: lead.score_breakdown.neighborhood_adoption_max },
                ].map(({ label, score, max }) => (
                  <div key={label}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">{label}</span>
                      <span className="text-xs font-medium text-gray-700">{score}/{max}</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-gray-200">
                      <div
                        className="h-2 rounded-full bg-solar-500 transition-all"
                        style={{ width: `${max > 0 ? (score / max) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="font-bold text-lg">{lead.score_breakdown.total_score}/100</span>
              </div>
            </div>
          )}

          {/* Contact Candidates */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Contact Candidates</h2>
            {lead.contact_candidates.length === 0 ? (
              <div>
                <p className="text-sm text-gray-400 mb-3">
                  No contacts discovered yet. Run enrichment to find contact information.
                </p>
                <button
                  onClick={handleEnrich}
                  disabled={enriching}
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  {enriching ? "Enriching..." : "Run Enrichment"}
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                {lead.contact_candidates.map((cc) => (
                  <div
                    key={cc.id}
                    className={cn(
                      "rounded-lg p-3 border",
                      cc.is_primary ? "bg-green-50 border-green-200" : "bg-gray-50 border-gray-200"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium uppercase",
                            cc.method === "phone"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-purple-100 text-purple-800"
                          )}
                        >
                          {cc.method}
                        </span>
                        <span className="text-sm font-medium text-gray-900">{cc.value}</span>
                      </div>
                      {cc.is_primary && (
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-medium text-green-800">
                          Primary
                        </span>
                      )}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs text-gray-500">
                      <span>Confidence: {Math.round(cc.confidence * 100)}%</span>
                      {cc.phone_type && <span>{cc.phone_type}</span>}
                      {cc.carrier_name && <span>{cc.carrier_name}</span>}
                      {cc.line_status && <span>{cc.line_status}</span>}
                      {cc.email_deliverable != null && (
                        <span className={cc.email_deliverable ? "text-green-600" : "text-red-600"}>
                          {cc.email_deliverable ? "Deliverable" : "Undeliverable"}
                        </span>
                      )}
                      {cc.validated && (
                        <span className="text-green-600">Validated</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Compliance Status */}
          <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Compliance Status</h2>
            <div className="space-y-2">
              {[
                { label: "Federal DNC", value: lead.compliance.federal_dnc },
                { label: "State DNC", value: lead.compliance.state_dnc },
                { label: "Internal DNC", value: lead.compliance.internal_dnc },
                { label: "Litigator Flag", value: lead.compliance.litigator_flag },
                { label: "Fraud Flag", value: lead.compliance.fraud_flag },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between rounded-lg bg-gray-50 p-2.5">
                  <span className="text-sm text-gray-600">{label}</span>
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                      value === "clear"
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    )}
                  >
                    {value === "clear" ? "Clear" : "Flagged"}
                  </span>
                </div>
              ))}
              <div className="flex items-center justify-between rounded-lg bg-gray-50 p-2.5">
                <span className="text-sm text-gray-600">Consent</span>
                <span
                  className={cn(
                    "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                    lead.compliance.consent_status === "explicit_opt_in"
                      ? "bg-green-100 text-green-800"
                      : lead.compliance.consent_status === "opted_out"
                      ? "bg-red-100 text-red-800"
                      : "bg-yellow-100 text-yellow-800"
                  )}
                >
                  {lead.compliance.consent_status.replace(/_/g, " ")}
                </span>
              </div>
            </div>
          </div>

          {/* Activate CTA */}
          {lead.status !== "activated" && (
            <button
              onClick={handleActivate}
              disabled={activating}
              className="w-full rounded-xl bg-solar-600 px-6 py-4 text-base font-semibold text-white hover:bg-solar-700 disabled:opacity-50 shadow-sm"
            >
              {activating ? "Activating..." : "Activate This Lead →"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
