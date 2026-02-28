// ============================================================
// LeadGen Types
// ============================================================

export interface SourceRecord {
  id: string;
  source_type: string;
  license: string;
  dataset_name: string;
  retrieval_method: string;
  retrieval_timestamp: string;
  evidence_fields: Record<string, string>;
  confidence: number;
  quality_score: number;
}

export interface SourceConfig {
  id: string;
  name: string;
  source_type: SourceType;
  license: LicenseType;
  license_detail: string | null;
  connector_class: string;
  config_json: Record<string, unknown>;
  ingestion_cadence: string | null;
  is_active: boolean;
  last_sync_at: string | null;
  last_sync_status: string | null;
  records_synced: number;
  created_at: string;
}

export type SourceType =
  | "tax_assessor"
  | "building_permit"
  | "utility_territory"
  | "solar_suitability"
  | "demographic_band"
  | "mls"
  | "contact_enrichment"
  | "byod_upload"
  | "vendor_feed";

export type LicenseType =
  | "public_record"
  | "public_data"
  | "vendor_feed"
  | "vendor_api"
  | "org_declared"
  | "mls_licensed";

export interface PermitRecord {
  id: string;
  permit_number: string;
  jurisdiction: string;
  category: string;
  raw_description: string | null;
  issue_date: string | null;
  final_date: string | null;
  status: string | null;
  contractor_name: string | null;
  estimated_cost: number | null;
}

export interface ContactCandidate {
  id: string;
  method: "phone" | "email";
  value: string;
  confidence: number;
  phone_type: string | null;
  carrier_name: string | null;
  line_status: string | null;
  email_deliverable: boolean | null;
  email_disposable: boolean | null;
  validated: boolean;
  is_primary: boolean;
}

export interface ComplianceStatus {
  federal_dnc: "clear" | "flagged";
  state_dnc: "clear" | "flagged";
  internal_dnc: "clear" | "flagged";
  consent_status: "explicit_opt_in" | "inferred" | "unknown" | "opted_out";
  litigator_flag: "clear" | "flagged";
  fraud_flag: "clear" | "flagged";
}

export interface DiscoveryScoreBreakdown {
  total_score: number;
  model_version: string;
  roof_suitability: number;
  roof_suitability_max: number;
  ownership_signal: number;
  ownership_signal_max: number;
  financial_capacity: number;
  financial_capacity_max: number;
  utility_economics: number;
  utility_economics_max: number;
  solar_potential: number;
  solar_potential_max: number;
  permit_triggers: number;
  permit_triggers_max: number;
  neighborhood_adoption: number;
  neighborhood_adoption_max: number;
  factor_details: Record<
    string,
    { points: number; max: number; reasoning: string; sources: string[] }
  >;
}

export type DiscoveryStatus =
  | "discovered"
  | "scoring"
  | "scored"
  | "enriching"
  | "enriched"
  | "activation_ready"
  | "activated"
  | "rejected"
  | "archived";

export interface DiscoveredLead {
  id: string;
  status: DiscoveryStatus;
  discovery_reason: string | null;
  discovery_batch: string | null;
  discovery_score: number | null;
  activation_score: number | null;
  enrichment_attempted: boolean;
  enrichment_at: string | null;
  best_phone: string | null;
  best_email: string | null;
  best_contact_confidence: number | null;
  activated_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  updated_at: string;
  // Joined data
  property: DiscoveredProperty;
  score_breakdown: DiscoveryScoreBreakdown | null;
  permits: PermitRecord[];
  source_records: SourceRecord[];
  contact_candidates: ContactCandidate[];
  compliance: ComplianceStatus;
}

export interface DiscoveredProperty {
  id: string;
  address_line1: string;
  address_line2: string | null;
  city: string;
  state: string;
  zip_code: string;
  county: string | null;
  latitude: number | null;
  longitude: number | null;
  parcel_id: string | null;
  property_type: string | null;
  year_built: number | null;
  building_sqft: number | null;
  lot_size_sqft: number | null;
  roof_area_sqft: number | null;
  assessed_value: number | null;
  last_sale_date: string | null;
  last_sale_price: number | null;
  owner_first_name: string | null;
  owner_last_name: string | null;
  owner_occupied: boolean | null;
  utility_name: string | null;
  utility_rate_zone: string | null;
  avg_rate_kwh: number | null;
  has_existing_solar: boolean;
  tree_cover_pct: number | null;
  neighborhood_solar_pct: number | null;
  median_household_income: number | null;
}

// List item (lighter than full detail)
export interface DiscoveredLeadRow {
  id: string;
  status: DiscoveryStatus;
  discovery_score: number | null;
  activation_score: number | null;
  address: string;
  city: string;
  state: string;
  county: string | null;
  property_type: string | null;
  year_built: number | null;
  roof_area_sqft: number | null;
  utility_name: string | null;
  has_existing_solar: boolean;
  owner_name: string | null;
  best_phone: string | null;
  best_phone_type: string | null;
  latitude: number | null;
  longitude: number | null;
  source_types: string[];
  has_permit: boolean;
  created_at: string;
}

export interface ActivationRow extends DiscoveredLeadRow {
  best_contact_confidence: number | null;
  dnc_status: "clear" | "flagged";
  consent_status: string;
}

export interface DiscoveredLeadListResponse {
  leads: DiscoveredLeadRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface SourceHealthEntry {
  source_id: string;
  name: string;
  source_type: SourceType;
  uptime_pct: number;
  last_7d_ingests: number[];
  last_error: string | null;
  last_error_at: string | null;
  avg_latency_ms: number;
  records_added_7d: number;
  records_updated_7d: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
}

export interface DiscoveryFilters {
  county?: string;
  min_score?: number;
  max_score?: number;
  status?: DiscoveryStatus | "";
  source_type?: SourceType | "";
  has_permit?: boolean;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

export interface ActivationFilters {
  min_discovery_score?: number;
  min_activation_score?: number;
  county?: string;
  page?: number;
  page_size?: number;
}
