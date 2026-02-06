const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (let browser set multipart boundary)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// Auth
export const api = {
  login: (email: string, password: string) =>
    request<{
      access_token: string;
      user_id: number;
      email: string;
      name: string;
      role: string;
    }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () =>
    request<{
      id: number;
      email: string;
      name: string;
      role: string;
      is_active: boolean;
    }>("/auth/me"),

  // Dashboard
  getKPIs: () =>
    request<{
      total_leads: number;
      hot_leads: number;
      warm_leads: number;
      cool_leads: number;
      appointments_scheduled: number;
      appointments_completed: number;
      total_outreach_attempts: number;
      avg_score: number | null;
      conversion_rate: number;
      status_breakdown: Record<string, number>;
    }>("/dashboard/kpis"),

  // Leads
  getLeads: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{
      leads: Array<{
        id: number;
        first_name: string | null;
        last_name: string | null;
        status: string;
        score: number | null;
        county: string | null;
        address: string | null;
        phone: string | null;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/leads${qs}`);
  },

  getLeadDetail: (id: number) =>
    request<{
      id: number;
      first_name: string | null;
      last_name: string | null;
      phone: string | null;
      email: string | null;
      status: string;
      assigned_rep_id: number | null;
      assigned_rep_name: string | null;
      total_call_attempts: number;
      total_sms_sent: number;
      total_emails_sent: number;
      last_contacted_at: string | null;
      created_at: string;
      updated_at: string;
      property: {
        id: number;
        address_line1: string;
        city: string;
        state: string;
        zip_code: string;
        county: string;
        property_type: string;
        year_built: number | null;
        roof_area_sqft: number | null;
        assessed_value: number | null;
        utility_zone: string | null;
        tree_cover_pct: number | null;
        has_existing_solar: boolean;
        owner_occupied: boolean;
        median_household_income: number | null;
      };
      scores: Array<{
        total_score: number;
        score_version: string;
        roof_age_score: number;
        ownership_score: number;
        roof_area_score: number;
        home_value_score: number;
        utility_rate_score: number;
        shade_score: number;
        neighborhood_score: number;
        income_score: number;
        property_type_score: number;
        existing_solar_score: number;
        scored_at: string;
      }>;
      recent_outreach: Array<{
        id: number;
        channel: string;
        disposition: string | null;
        started_at: string;
        duration_seconds: number | null;
      }>;
      notes: Array<{
        id: number;
        author: string;
        content: string;
        created_at: string;
      }>;
      consent_logs: Array<{
        id: number;
        consent_type: string;
        status: string;
        channel: string;
        evidence_type: string | null;
        recorded_at: string;
      }>;
    }>(`/leads/${id}`),

  scoreLead: (id: number) =>
    request<{
      lead_id: number;
      total_score: number;
      tier: string;
      factors: Record<string, number>;
    }>(`/leads/${id}/score`, { method: "POST" }),

  updateLeadStatus: (id: number, status: string) =>
    request(`/leads/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  assignRep: (leadId: number, repId: number) =>
    request(`/leads/${leadId}/assign`, {
      method: "PATCH",
      body: JSON.stringify({ rep_id: repId }),
    }),

  addNote: (leadId: number, content: string, author: string = "user") =>
    request(`/leads/${leadId}/notes`, {
      method: "POST",
      body: JSON.stringify({ content, author }),
    }),

  uploadCSV: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ ingested: number; skipped: number; errors: string[] }>(
      "/leads/ingest/csv",
      { method: "POST", body: formData }
    );
  },

  // Outreach
  enqueueOutreach: (leadId: number) =>
    request(`/outreach/${leadId}/enqueue`, { method: "POST" }),

  // Appointments
  getAppointments: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<
      Array<{
        id: number;
        lead_id: number;
        rep_id: number;
        rep_name: string | null;
        status: string;
        scheduled_start: string;
        scheduled_end: string;
        address: string | null;
        notes: string | null;
      }>
    >(`/appointments${qs}`);
  },

  createAppointment: (data: {
    lead_id: number;
    rep_id: number;
    scheduled_start: string;
    scheduled_end: string;
    notes?: string;
  }) =>
    request("/appointments", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Admin
  getAuditLog: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<
      Array<{
        id: number;
        actor: string;
        action: string;
        entity_type: string;
        entity_id: number | null;
        old_value: string | null;
        new_value: string | null;
        created_at: string;
      }>
    >(`/admin/audit-log${qs}`);
  },

  getScripts: () =>
    request<
      Array<{
        id: number;
        version_label: string;
        channel: string;
        content: string | null;
        is_active: boolean;
        created_by: string | null;
        created_at: string;
      }>
    >("/admin/scripts"),

  getReps: () =>
    request<
      Array<{
        id: number;
        email: string;
        name: string;
        phone: string | null;
        role: string;
        is_active: boolean;
      }>
    >("/admin/reps"),
};
