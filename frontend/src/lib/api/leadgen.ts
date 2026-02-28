import type {
  DiscoveredLead,
  DiscoveredLeadListResponse,
  ActivationRow,
  SourceConfig,
  SourceHealthEntry,
  DiscoveryFilters,
  ActivationFilters,
} from "@/lib/types/leadgen";

// ============================================================
// Config
// ============================================================

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData))
    headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ============================================================
// Public API
// ============================================================

export const leadgenApi = {
  // ---- Discovery ----

  listDiscoveredLeads: async (
    filters: DiscoveryFilters = {}
  ): Promise<DiscoveredLeadListResponse> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v != null && v !== "") params.set(k, String(v));
    });
    return request(`/discovered?${params}`);
  },

  getDiscoveredLead: async (id: string): Promise<DiscoveredLead> => {
    return request(`/discovered/${id}`);
  },

  enrichDiscoveredLead: async (
    id: string
  ): Promise<{ status: string }> => {
    return request(`/discovered/${id}/enrich`, { method: "POST" });
  },

  skipTrace: async (
    limit: number,
    filters: { county?: string; min_score?: number } = {}
  ): Promise<{ status: string; submitted: number; found: number; not_found: number; activated: number }> => {
    return request("/discovered/skip-trace", {
      method: "POST",
      body: JSON.stringify({
        limit,
        auto_activate: true,
        ...filters,
      }),
    });
  },

  runFullPipeline: async (
    county: string,
    opts: { discovery_limit?: number; trace_limit?: number; min_score?: number } = {}
  ): Promise<{
    status: string;
    discovered: number;
    scored: number;
    skipped: number;
    traced: number;
    phones_found: number;
    activated: number;
  }> => {
    return request("/discovered/full-pipeline", {
      method: "POST",
      body: JSON.stringify({
        county,
        discovery_limit: opts.discovery_limit ?? 1000,
        trace_limit: opts.trace_limit ?? 100,
        min_score: opts.min_score ?? 50,
      }),
    });
  },

  runDiscovery: async (
    county: string,
    limit: number = 1000
  ): Promise<{ status: string; ingested: number; scored: number; skipped: number; errors: number }> => {
    return request("/discovered/run", {
      method: "POST",
      body: JSON.stringify({ county, limit }),
    });
  },

  activateDiscoveredLead: async (
    id: string
  ): Promise<{ lead_id: string; status: string }> => {
    return request(`/activate/${id}`, { method: "POST" });
  },

  // ---- Activation Queue ----

  listActivationQueue: async (
    filters: ActivationFilters = {}
  ): Promise<{ leads: ActivationRow[]; total: number }> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (v != null && v !== "") params.set(k, String(v));
    });
    return request(`/activate/queue?${params}`);
  },

  approveActivation: async (
    ids: string[]
  ): Promise<{ activated: number }> => {
    return request("/activate/batch", {
      method: "POST",
      body: JSON.stringify({ discovered_lead_ids: ids }),
    });
  },

  rejectActivation: async (
    id: string,
    reason: string
  ): Promise<{ status: string }> => {
    return request(`/activate/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
  },

  // ---- Sources ----

  listSources: async (): Promise<SourceConfig[]> => {
    return request("/sources");
  },

  syncSource: async (id: string): Promise<{ status: string }> => {
    return request(`/sources/${id}/sync`, { method: "POST" });
  },

  testSourceConnection: async (
    payload: Record<string, unknown>
  ): Promise<{ success: boolean; message: string; record_count?: number }> => {
    return request("/sources/test-connection", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // ---- Source Health ----

  getSourceHealth: async (): Promise<SourceHealthEntry[]> => {
    return request("/admin/source-health");
  },
};
