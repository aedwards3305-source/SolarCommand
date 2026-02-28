const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

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
    throw new ApiError(body.detail || `HTTP ${res.status}`, res.status);
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

  // Messages (SMS thread)
  getMessages: (leadId: number) =>
    request<
      Array<{
        id: number;
        direction: string;
        channel: string;
        from_number: string | null;
        to_number: string | null;
        body: string;
        ai_intent: string | null;
        ai_suggested_reply: string | null;
        sent_by: string | null;
        created_at: string;
      }>
    >(`/leads/${leadId}/messages`),

  sendMessage: (leadId: number, message: string) =>
    request<{ status: string; message_id: number }>(`/leads/${leadId}/messages/send`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  // QA
  getLeadQA: (leadId: number) =>
    request<
      Array<{
        id: number;
        lead_id: number;
        conversation_id: number | null;
        compliance_score: number;
        flags: Array<{ flag: string; severity: string; evidence?: string }> | null;
        checklist_pass: boolean;
        rationale: string | null;
        reviewed_by: string;
        created_at: string;
      }>
    >(`/leads/${leadId}/qa`),

  getQAQueue: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<
      Array<{
        id: number;
        lead_id: number;
        lead_name: string;
        conversation_id: number | null;
        compliance_score: number;
        flags: Array<{ flag: string; severity: string }> | null;
        checklist_pass: boolean;
        reviewed_by: string;
        created_at: string;
      }>
    >(`/admin/qa${qs}`);
  },

  // NBA
  getLeadNBA: (leadId: number) =>
    request<{
      id: number;
      lead_id: number;
      recommended_action: string;
      recommended_channel: string | null;
      schedule_time: string | null;
      reason_codes: string[] | null;
      confidence: number;
      applied: boolean;
      expires_at: string | null;
      created_at: string;
    } | null>(`/leads/${leadId}/nba`),

  recomputeNBA: (leadId: number) =>
    request<{ status: string }>(`/leads/${leadId}/nba/recompute`, { method: "POST" }),

  // Script Experiments
  getExperiments: () =>
    request<
      Array<{
        id: number;
        name: string;
        channel: string;
        control_sends: number;
        variant_sends: number;
        control_responses: number;
        variant_responses: number;
        control_conversions: number;
        variant_conversions: number;
        is_active: boolean;
        started_at: string;
        control_response_rate: number;
        variant_response_rate: number;
        control_conversion_rate: number;
        variant_conversion_rate: number;
      }>
    >("/admin/scripts/experiments"),

  suggestScript: (scriptId: number) =>
    request<{
      edits: Array<{ line: string; replacement: string; rationale: string }>;
      hypotheses: string[];
      expected_lift: number;
    }>(`/admin/scripts/${scriptId}/suggest`, { method: "POST" }),

  // Dashboard Insights
  getInsights: () =>
    request<{
      narrative: string;
      key_drivers: string[];
      recommendations: string[];
    }>("/dashboard/insights"),

  // AI Operator
  getRepBrief: (leadId: number) =>
    request<{
      summary: string;
      talk_track: string[];
      objection_handlers: string[];
      recommended_approach: string;
      risk_factors: string[] | null;
    }>(`/ai/leads/${leadId}/rep-brief`),

  getRepBriefResult: (leadId: number) =>
    request<{
      summary: string;
      talk_track: string[];
      objection_handlers: string[];
      recommended_approach: string;
      risk_factors: string[] | null;
    }>(`/ai/leads/${leadId}/rep-brief/result`),

  getLeadObjections: (leadId: number) =>
    request<
      Array<{
        id: number;
        tag: string;
        confidence: number;
        evidence_span: string | null;
        created_at: string;
      }>
    >(`/ai/leads/${leadId}/objections`),

  getAIRuns: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{
      runs: Array<{
        id: number;
        task_type: string;
        lead_id: number | null;
        conversation_id: number | null;
        model: string;
        temperature: number | null;
        prompt_version: string | null;
        tokens_in: number;
        tokens_out: number;
        cost_usd: number | null;
        latency_ms: number | null;
        status: string;
        error: string | null;
        created_at: string;
      }>;
      total: number;
    }>(`/ai/admin/runs${qs}`);
  },

  getAIRunDetail: (runId: number) =>
    request<{
      id: number;
      task_type: string;
      lead_id: number | null;
      conversation_id: number | null;
      model: string;
      temperature: number | null;
      prompt_version: string | null;
      input_json: Record<string, unknown> | null;
      output_json: Record<string, unknown> | null;
      tokens_in: number;
      tokens_out: number;
      cost_usd: number | null;
      latency_ms: number | null;
      status: string;
      error: string | null;
      created_at: string;
    }>(`/ai/admin/runs/${runId}`),

  getAIStats: () =>
    request<{
      total_runs_today: number;
      errors_today: number;
      avg_latency_ms: number;
      total_cost_today: number;
      runs_by_task: Record<string, number>;
    }>("/ai/admin/stats"),

  suggestScriptAI: (scriptId: number) =>
    request<{
      edits: Array<{ line: string; replacement: string; rationale: string }>;
      hypotheses: string[];
      expected_lift: number;
    }>(`/ai/admin/scripts/${scriptId}/suggest`, { method: "POST" }),

  // Voice
  placeVoiceCall: (leadId: number, scriptVersionId?: number) =>
    request<{ status: string; lead_id: number }>(`/ai/leads/${leadId}/voice/call`, {
      method: "POST",
      body: JSON.stringify({ script_version_id: scriptVersionId || null }),
    }),

  getLeadRecordings: (leadId: number) =>
    request<
      Array<{
        id: number;
        call_sid: string | null;
        provider: string | null;
        recording_url: string | null;
        duration_seconds: number | null;
        call_status: string | null;
        ai_summary: string | null;
        ai_sentiment: string | null;
        created_at: string;
      }>
    >(`/ai/leads/${leadId}/voice/recordings`),

  // Enrichment
  getLeadEnrichment: (leadId: number) =>
    request<{
      enrichment: {
        provider: string;
        full_name: string | null;
        emails: Array<{ email: string; type: string }> | null;
        phones: Array<{ number: string; type: string }> | null;
        job_title: string | null;
        linkedin_url: string | null;
        confidence: number;
        updated_at: string;
      } | null;
      validation: {
        provider: string;
        phone_valid: boolean | null;
        phone_type: string | null;
        phone_carrier: string | null;
        email_valid: boolean | null;
        email_deliverable: boolean | null;
        address_valid: boolean | null;
        confidence: number;
        updated_at: string;
      } | null;
    }>(`/ai/leads/${leadId}/enrichment`),

  runEnrichment: (leadId: number) =>
    request<{ status: string; lead_id: number }>(`/ai/leads/${leadId}/enrichment/run`, {
      method: "POST",
    }),

  // Cost Center
  getCostSummary: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{
      month: string;
      total_cost: number;
      ai_cost: number;
      voice_cost: number;
      ai_run_count: number;
      voice_call_count: number;
      daily_totals: Array<{ date: string; ai_cost: number; voice_cost: number }>;
    }>(`/admin/cost-center/summary${qs}`);
  },

  getCostItems: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{
      items: Array<{
        id: string;
        category: string;
        timestamp: string;
        description: string;
        lead_id: number | null;
        detail: string;
        cost_usd: number;
      }>;
      total: number;
      has_more: boolean;
    }>(`/admin/cost-center/items${qs}`);
  },
};
