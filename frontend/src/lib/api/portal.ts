/**
 * Portal API client — public endpoints, NO auth token required.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function portalRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ── Types ────────────────────────────────────────────────────────────────

export interface PortalLead {
  first_name: string | null;
  last_name: string | null;
  address: string;
  solar_score: number | null;
  status: string;
  savings: {
    system_size_kw: number;
    panel_count: number;
    annual_savings: number;
    lifetime_savings: number;
    federal_tax_credit: number;
    monthly_savings: number;
  };
  appointments: Array<{
    id: number;
    status: string;
    scheduled_start: string;
    scheduled_end: string;
    address: string | null;
    notes: string | null;
  }>;
}

interface QuoteData {
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
}

interface AppointmentData {
  preferred_date: string;
  time_preference: string;
  notes?: string;
}

// ── API Methods ──────────────────────────────────────────────────────────

export const portalApi = {
  submitQuote: (data: QuoteData) =>
    portalRequest<{ token: string; message: string }>("/portal/quote", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getLeadSummary: (token: string) =>
    portalRequest<PortalLead>(`/portal/lead/${token}`),

  requestAppointment: (token: string, data: AppointmentData) =>
    portalRequest<{
      appointment_id: number;
      scheduled_start: string;
      scheduled_end: string;
      message: string;
    }>(`/portal/lead/${token}/appointment`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getAppointments: (token: string) =>
    portalRequest<{
      appointments: Array<{
        id: number;
        status: string;
        scheduled_start: string;
        scheduled_end: string;
        address: string | null;
        notes: string | null;
      }>;
    }>(`/portal/lead/${token}/appointments`),

  sendMessage: (token: string, body: string) =>
    portalRequest<{ message_id: number; created_at: string; message: string }>(
      `/portal/lead/${token}/message`,
      { method: "POST", body: JSON.stringify({ body }) }
    ),
};
