"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { portalApi, type PortalLead } from "@/lib/api/portal";
import { formatCurrency } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-800",
  confirmed: "bg-green-100 text-green-800",
  completed: "bg-gray-100 text-gray-800",
  cancelled: "bg-red-100 text-red-800",
  no_show: "bg-yellow-100 text-yellow-800",
  rescheduled: "bg-purple-100 text-purple-800",
};

function getNextTwoWeeks(): string[] {
  const dates: string[] = [];
  const today = new Date();
  for (let i = 1; i <= 14; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    if (d.getDay() !== 0) {
      // exclude Sundays
      dates.push(d.toISOString().split("T")[0]);
    }
  }
  return dates;
}

function formatDateLabel(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

function formatAppointmentTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function LeadPortalPage() {
  const { token } = useParams<{ token: string }>();
  const [lead, setLead] = useState<PortalLead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Scheduling state
  const [selectedDate, setSelectedDate] = useState("");
  const [timePref, setTimePref] = useState<"morning" | "afternoon" | "evening">("morning");
  const [apptNotes, setApptNotes] = useState("");
  const [scheduling, setScheduling] = useState(false);
  const [scheduleSuccess, setScheduleSuccess] = useState("");

  // Message state
  const [messageBody, setMessageBody] = useState("");
  const [sending, setSending] = useState(false);
  const [messageSent, setMessageSent] = useState(false);

  const dates = getNextTwoWeeks();

  useEffect(() => {
    if (!token) return;
    portalApi
      .getLeadSummary(token)
      .then(setLead)
      .catch((e) => setError(e instanceof Error ? e.message : "Unable to load your portal"))
      .finally(() => setLoading(false));
  }, [token]);

  const handleSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDate || !token) return;
    setScheduling(true);
    setScheduleSuccess("");
    try {
      const res = await portalApi.requestAppointment(token, {
        preferred_date: selectedDate,
        time_preference: timePref,
        notes: apptNotes || undefined,
      });
      setScheduleSuccess(res.message);
      // Reload lead data to show new appointment
      const updated = await portalApi.getLeadSummary(token);
      setLead(updated);
      setSelectedDate("");
      setApptNotes("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to schedule");
    } finally {
      setScheduling(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageBody.trim() || !token) return;
    setSending(true);
    try {
      await portalApi.sendMessage(token, messageBody.trim());
      setMessageSent(true);
      setMessageBody("");
      setTimeout(() => setMessageSent(false), 5000);
    } catch {
      setError("Failed to send message");
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="animate-pulse text-gray-400">
          Loading your solar portal...
        </div>
      </div>
    );
  }

  if (error && !lead) {
    return (
      <div className="mx-auto max-w-xl px-4 py-20 text-center">
        <div className="rounded-2xl bg-white p-8 shadow-sm border border-gray-200">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600">
            <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <h2 className="mt-4 text-xl font-bold text-gray-900">
            Link Not Found
          </h2>
          <p className="mt-2 text-sm text-gray-500">
            This portal link is invalid or has expired.
          </p>
          <a
            href="/solar"
            className="mt-6 inline-block rounded-lg bg-solar-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-solar-700 transition-colors"
          >
            Request a New Quote
          </a>
        </div>
      </div>
    );
  }

  if (!lead) return null;

  const { savings } = lead;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12 space-y-8">
      {/* Welcome */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
          Welcome, {lead.first_name}!
        </h1>
        <p className="mt-1 text-gray-500">{lead.address}</p>
        {lead.solar_score && (
          <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-solar-100 px-4 py-1.5 text-sm font-semibold text-solar-800">
            <svg width={16} height={16} className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
            </svg>
            Solar Score: {lead.solar_score}/100
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Estimated Savings */}
      <div className="rounded-2xl bg-gradient-to-br from-solar-600 to-solar-800 p-6 text-white sm:p-8">
        <h2 className="text-lg font-semibold">Your Estimated Solar Savings</h2>
        <p className="mt-1 text-sm text-solar-200">
          Sunburst Solar system with 25-year warranty &amp; production guarantee
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl bg-white/10 p-4 text-center backdrop-blur-sm">
            <p className="text-2xl font-extrabold sm:text-3xl">
              {formatCurrency(savings.annual_savings)}
            </p>
            <p className="mt-1 text-xs text-solar-200">Annual Savings</p>
          </div>
          <div className="rounded-xl bg-white/10 p-4 text-center backdrop-blur-sm">
            <p className="text-2xl font-extrabold sm:text-3xl">
              {formatCurrency(savings.lifetime_savings)}
            </p>
            <p className="mt-1 text-xs text-solar-200">25-Year Savings</p>
          </div>
          <div className="rounded-xl bg-white/10 p-4 text-center backdrop-blur-sm">
            <p className="text-2xl font-extrabold sm:text-3xl">
              {formatCurrency(savings.federal_tax_credit)}
            </p>
            <p className="mt-1 text-xs text-solar-200">30% Federal Tax Credit</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap justify-center gap-4 text-xs text-solar-200">
          <span>{savings.system_size_kw} kW system</span>
          <span>{savings.panel_count} panels</span>
          <span>{formatCurrency(savings.monthly_savings)}/mo savings</span>
          <span>Enphase battery available</span>
        </div>
      </div>

      {/* Additional Services */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl bg-white p-5 shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sunburst-100 text-sunburst-600">
              <svg width={18} height={18} className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Panel Cleaning</h3>
              <p className="text-xs text-gray-500">
                Keep your system at peak efficiency. Dirty panels lose 15–25% output.
              </p>
            </div>
          </div>
        </div>
        <div className="rounded-2xl bg-white p-5 shadow-sm border border-gray-200">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-100 text-green-600">
              <svg width={18} height={18} className="h-[18px] w-[18px]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">Electricity Bill Audit</h3>
              <p className="text-xs text-gray-500">
                We review 36 months of bills to find overcharges and recover your refund.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Consultation */}
      <div className="rounded-2xl bg-white p-6 shadow-sm border border-gray-200 sm:p-8">
        <h2 className="text-lg font-semibold text-gray-900">
          Schedule Your Free Consultation
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Pick a date and time that works for you. We&apos;ll confirm via text.
        </p>

        {scheduleSuccess && (
          <div className="mt-4 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
            {scheduleSuccess}
          </div>
        )}

        <form onSubmit={handleSchedule} className="mt-4 space-y-4">
          {/* Date picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Preferred Date
            </label>
            <div className="flex flex-wrap gap-2">
              {dates.map((d) => (
                <button
                  type="button"
                  key={d}
                  onClick={() => setSelectedDate(d)}
                  className={`rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                    selectedDate === d
                      ? "bg-solar-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {formatDateLabel(d)}
                </button>
              ))}
            </div>
          </div>

          {/* Time preference */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Preference
            </label>
            <div className="flex gap-3">
              {(
                [
                  { value: "morning", label: "Morning", sub: "8am – 12pm" },
                  { value: "afternoon", label: "Afternoon", sub: "12pm – 4pm" },
                  { value: "evening", label: "Evening", sub: "4pm – 6pm" },
                ] as const
              ).map((opt) => (
                <button
                  type="button"
                  key={opt.value}
                  onClick={() => setTimePref(opt.value)}
                  className={`flex-1 rounded-lg border p-3 text-center transition-colors ${
                    timePref === opt.value
                      ? "border-solar-500 bg-solar-50 text-solar-700"
                      : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  <div className="text-sm font-medium">{opt.label}</div>
                  <div className="text-[10px] text-gray-400">{opt.sub}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes (optional)
            </label>
            <textarea
              value={apptNotes}
              onChange={(e) => setApptNotes(e.target.value)}
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none resize-none"
              placeholder="Anything we should know?"
            />
          </div>

          <button
            type="submit"
            disabled={!selectedDate || scheduling}
            className="w-full rounded-lg bg-solar-600 px-6 py-3 text-sm font-bold text-white hover:bg-solar-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {scheduling ? "Scheduling..." : "Schedule My Free Consultation"}
          </button>
        </form>
      </div>

      {/* Existing Appointments */}
      {lead.appointments.length > 0 && (
        <div className="rounded-2xl bg-white p-6 shadow-sm border border-gray-200 sm:p-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Your Appointments
          </h2>
          <div className="space-y-3">
            {lead.appointments.map((apt) => (
              <div
                key={apt.id}
                className="flex items-center justify-between rounded-xl bg-gray-50 p-4"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {formatAppointmentTime(apt.scheduled_start)}
                  </p>
                  {apt.address && (
                    <p className="text-xs text-gray-500 mt-0.5">
                      {apt.address}
                    </p>
                  )}
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    STATUS_COLORS[apt.status] || "bg-gray-100 text-gray-800"
                  }`}
                >
                  {apt.status.charAt(0).toUpperCase() + apt.status.slice(1)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Message Us */}
      <div className="rounded-2xl bg-white p-6 shadow-sm border border-gray-200 sm:p-8">
        <h2 className="text-lg font-semibold text-gray-900">Message Us</h2>
        <p className="mt-1 text-sm text-gray-500">
          Our team typically responds within 1 business day.
        </p>

        {messageSent && (
          <div className="mt-3 rounded-lg bg-green-50 border border-green-200 p-3 text-sm text-green-700">
            Message sent! We&apos;ll get back to you soon.
          </div>
        )}

        <form onSubmit={handleSendMessage} className="mt-4">
          <textarea
            value={messageBody}
            onChange={(e) => setMessageBody(e.target.value)}
            rows={3}
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-solar-500 outline-none resize-none"
            placeholder="Have a question? Let us know..."
          />
          <button
            type="submit"
            disabled={!messageBody.trim() || sending}
            className="mt-3 rounded-lg bg-gray-900 px-5 py-2 text-sm font-medium text-white hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sending ? "Sending..." : "Send Message"}
          </button>
        </form>
      </div>
    </div>
  );
}
