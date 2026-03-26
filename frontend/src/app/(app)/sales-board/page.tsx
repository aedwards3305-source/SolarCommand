"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn, formatDateTime, formatDate } from "@/lib/utils";

/* ── Types ─────────────────────────────────────────────────────────────── */

interface SalesStats {
  appointments_today: number;
  appointments_this_week: number;
  appointments_completed: number;
  appointments_no_show: number;
  my_total_leads: number;
  my_hot_leads: number;
  my_warm_leads: number;
  my_qualified_leads: number;
  my_appointment_set: number;
  closed_won: number;
  closed_lost: number;
  close_rate: number;
  total_outreach: number;
  calls_made: number;
  sms_sent: number;
  emails_sent: number;
  follow_ups_due_today: number;
  avg_lead_score: number | null;
}

interface AppointmentDetail {
  id: number;
  lead_id: number;
  lead_name: string | null;
  lead_phone: string | null;
  address: string | null;
  status: string;
  scheduled_start: string;
  scheduled_end: string;
  notes: string | null;
  lead_score: number | null;
}

interface MyAppointments {
  today: AppointmentDetail[];
  upcoming: AppointmentDetail[];
  recent_completed: AppointmentDetail[];
}

interface PipelineStage {
  stage: string;
  label: string;
  count: number;
  leads: Array<{ id: number; name: string; phone: string | null; created_at: string | null }>;
}

interface Pipeline {
  stages: PipelineStage[];
  total_pipeline_leads: number;
}

interface ActivityItem {
  id: number;
  type: string;
  description: string;
  lead_id: number | null;
  lead_name: string | null;
  timestamp: string;
  meta: Record<string, string> | null;
}

interface LeaderboardEntry {
  rep_id: number;
  rep_name: string;
  closed_won: number;
  appointments_completed: number;
  total_leads: number;
}

/* ── Helpers ───────────────────────────────────────────────────────────── */

function scoreColor(score: number | null) {
  if (score == null) return "text-gray-400";
  if (score >= 75) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-500";
}

function apptStatusBadge(status: string) {
  const map: Record<string, string> = {
    scheduled: "bg-blue-100 text-blue-700",
    confirmed: "bg-green-100 text-green-700",
    completed: "bg-emerald-100 text-emerald-700",
    no_show: "bg-red-100 text-red-700",
    cancelled: "bg-gray-100 text-gray-500",
    rescheduled: "bg-yellow-100 text-yellow-700",
  };
  return map[status] || "bg-gray-100 text-gray-700";
}

function activityIcon(type: string) {
  const icons: Record<string, string> = {
    outreach: "M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z",
    appointment: "M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5",
    note: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
  };
  return icons[type] || icons.note;
}

const activityColor: Record<string, string> = {
  outreach: "text-blue-500",
  appointment: "text-green-500",
  note: "text-gray-400",
};

const stageColors: Record<string, string> = {
  hot: "border-red-400 bg-red-50",
  warm: "border-orange-400 bg-orange-50",
  contacting: "border-yellow-400 bg-yellow-50",
  contacted: "border-yellow-300 bg-yellow-50",
  qualified: "border-green-400 bg-green-50",
  appointment_set: "border-emerald-400 bg-emerald-50",
  nurturing: "border-purple-400 bg-purple-50",
  closed_won: "border-emerald-600 bg-emerald-50",
  closed_lost: "border-gray-400 bg-gray-50",
};

/* ── Main Page ─────────────────────────────────────────────────────────── */

export default function SalesBoardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<SalesStats | null>(null);
  const [appointments, setAppointments] = useState<MyAppointments | null>(null);
  const [pipeline, setPipeline] = useState<Pipeline | null>(null);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<"today" | "upcoming" | "completed">("today");

  const load = useCallback(() => {
    api.getSalesStats().then(setStats).catch((e) => setError(e.message));
    api.getMyAppointments().then(setAppointments).catch(() => {});
    api.getMyPipeline().then(setPipeline).catch(() => {});
    api.getMyActivity(25).then(setActivity).catch(() => {});
    api.getLeaderboard().then(setLeaderboard).catch(() => {});
  }, []);

  useEffect(() => { load(); }, [load]);

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-700">
        Failed to load sales board: {error}
      </div>
    );
  }

  if (!stats) {
    return <div className="animate-pulse text-gray-400">Loading your sales board...</div>;
  }

  const showRate = stats.appointments_completed + stats.appointments_no_show;
  const showUpRate = showRate > 0
    ? Math.round((stats.appointments_completed / showRate) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sales Board</h1>
          <p className="text-sm text-gray-500 mt-1">
            Welcome back, {user?.name || "Rep"}. Here&apos;s your command center.
          </p>
        </div>
        <button
          onClick={load}
          className="rounded-lg bg-solar-600 px-4 py-2 text-sm font-medium text-white hover:bg-solar-700 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* ── Top KPI Row ── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <KPICard label="Today's Appts" value={stats.appointments_today} color="bg-solar-500" />
        <KPICard label="This Week" value={stats.appointments_this_week} color="bg-blue-500" />
        <KPICard label="Follow-ups Due" value={stats.follow_ups_due_today} color="bg-amber-500" urgent={stats.follow_ups_due_today > 0} />
        <KPICard label="Closed Won" value={stats.closed_won} color="bg-emerald-500" />
        <KPICard label="Close Rate" value={`${stats.close_rate}%`} color="bg-green-600" />
        <KPICard label="My Leads" value={stats.my_total_leads} color="bg-purple-500" />
      </div>

      {/* ── Second Row: Detailed Stats ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Appointment Performance */}
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Appointment Performance</h3>
          <div className="space-y-3">
            <StatRow label="Completed" value={stats.appointments_completed} />
            <StatRow label="No-Shows" value={stats.appointments_no_show} bad={stats.appointments_no_show > 0} />
            <StatRow label="Show-up Rate" value={`${showUpRate}%`} good={showUpRate >= 80} />
            <StatRow label="Appt Set" value={stats.my_appointment_set} />
          </div>
        </div>

        {/* Lead Breakdown */}
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">My Lead Breakdown</h3>
          <div className="space-y-3">
            <StatRow label="🔴 Hot" value={stats.my_hot_leads} />
            <StatRow label="🟠 Warm" value={stats.my_warm_leads} />
            <StatRow label="✅ Qualified" value={stats.my_qualified_leads} />
            <StatRow label="Won / Lost" value={`${stats.closed_won} / ${stats.closed_lost}`} />
            {stats.avg_lead_score != null && (
              <StatRow label="Avg Score" value={stats.avg_lead_score} />
            )}
          </div>
        </div>

        {/* Outreach Summary */}
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Outreach Activity</h3>
          <div className="space-y-3">
            <StatRow label="Total Touches" value={stats.total_outreach} />
            <StatRow label="Calls" value={stats.calls_made} />
            <StatRow label="SMS" value={stats.sms_sent} />
            <StatRow label="Emails" value={stats.emails_sent} />
          </div>
        </div>
      </div>

      {/* ── Appointments Board ── */}
      <div className="rounded-xl bg-white shadow-sm border border-gray-200">
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3">
          <h3 className="text-lg font-semibold text-gray-900">My Appointments</h3>
          <div className="flex gap-1">
            {(["today", "upcoming", "completed"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                  tab === t
                    ? "bg-solar-600 text-white"
                    : "text-gray-500 hover:bg-gray-100"
                )}
              >
                {t === "today" ? `Today (${appointments?.today.length ?? 0})` :
                 t === "upcoming" ? `Upcoming (${appointments?.upcoming.length ?? 0})` :
                 `Completed (${appointments?.recent_completed.length ?? 0})`}
              </button>
            ))}
          </div>
        </div>
        <div className="p-5">
          {!appointments ? (
            <p className="text-sm text-gray-400 animate-pulse">Loading...</p>
          ) : (
            <AppointmentList
              items={
                tab === "today" ? appointments.today :
                tab === "upcoming" ? appointments.upcoming :
                appointments.recent_completed
              }
              emptyMessage={
                tab === "today" ? "No appointments today — time to book some!" :
                tab === "upcoming" ? "No upcoming appointments in the next 7 days." :
                "No recently completed appointments."
              }
            />
          )}
        </div>
      </div>

      {/* ── Pipeline + Activity + Leaderboard ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Pipeline Kanban */}
        <div className="lg:col-span-2 rounded-xl bg-white shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">My Pipeline</h3>
            {pipeline && (
              <span className="text-sm text-gray-500">
                {pipeline.total_pipeline_leads} leads total
              </span>
            )}
          </div>
          {!pipeline ? (
            <p className="text-sm text-gray-400 animate-pulse">Loading pipeline...</p>
          ) : (
            <div className="flex gap-3 overflow-x-auto pb-2">
              {pipeline.stages.filter(s => s.count > 0).map((stage) => (
                <div
                  key={stage.stage}
                  className={cn(
                    "min-w-[160px] flex-shrink-0 rounded-lg border-l-4 p-3",
                    stageColors[stage.stage] || "border-gray-300 bg-gray-50"
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold uppercase text-gray-600">
                      {stage.label}
                    </span>
                    <span className="rounded-full bg-white px-2 py-0.5 text-xs font-bold text-gray-700 shadow-sm">
                      {stage.count}
                    </span>
                  </div>
                  <div className="space-y-1.5">
                    {stage.leads.slice(0, 5).map((lead) => (
                      <Link
                        key={lead.id}
                        href={`/leads/${lead.id}`}
                        className="block rounded-md bg-white p-2 text-xs shadow-sm hover:shadow transition-shadow border border-gray-100"
                      >
                        <span className="font-medium text-gray-800">{lead.name}</span>
                        {lead.phone && (
                          <span className="block text-gray-400 mt-0.5">{lead.phone}</span>
                        )}
                      </Link>
                    ))}
                    {stage.count > 5 && (
                      <p className="text-xs text-gray-400 text-center pt-1">
                        +{stage.count - 5} more
                      </p>
                    )}
                  </div>
                </div>
              ))}
              {pipeline.stages.every(s => s.count === 0) && (
                <p className="text-sm text-gray-400">No leads in your pipeline yet.</p>
              )}
            </div>
          )}
        </div>

        {/* Leaderboard */}
        <div className="rounded-xl bg-white shadow-sm border border-gray-200 p-5">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Team Leaderboard</h3>
          {leaderboard.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet.</p>
          ) : (
            <div className="space-y-3">
              {leaderboard.map((entry, i) => (
                <div
                  key={entry.rep_id}
                  className={cn(
                    "flex items-center gap-3 rounded-lg p-3",
                    entry.rep_id === user?.id ? "bg-solar-50 border border-solar-200" : "bg-gray-50"
                  )}
                >
                  <span className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold",
                    i === 0 ? "bg-yellow-400 text-yellow-900" :
                    i === 1 ? "bg-gray-300 text-gray-700" :
                    i === 2 ? "bg-orange-300 text-orange-800" :
                    "bg-gray-100 text-gray-500"
                  )}>
                    {i + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {entry.rep_name}
                      {entry.rep_id === user?.id && (
                        <span className="ml-1 text-xs text-solar-600">(You)</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-500">
                      {entry.total_leads} leads
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-emerald-600">{entry.closed_won} won</p>
                    <p className="text-xs text-gray-400">{entry.appointments_completed} appts</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Activity Feed ── */}
      <div className="rounded-xl bg-white shadow-sm border border-gray-200 p-5">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        {activity.length === 0 ? (
          <p className="text-sm text-gray-400">No recent activity.</p>
        ) : (
          <div className="space-y-3">
            {activity.map((item, idx) => (
              <div key={`${item.type}-${item.id}-${idx}`} className="flex items-start gap-3">
                <div className={cn("mt-0.5 flex-shrink-0", activityColor[item.type] || "text-gray-400")}>
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d={activityIcon(item.type)} />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {item.lead_id && (
                      <Link
                        href={`/leads/${item.lead_id}`}
                        className="text-sm font-medium text-solar-600 hover:underline"
                      >
                        {item.lead_name}
                      </Link>
                    )}
                    <span className="text-xs text-gray-400">
                      {formatDateTime(item.timestamp)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-0.5">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Sub-components ────────────────────────────────────────────────────── */

function KPICard({
  label,
  value,
  color,
  urgent,
}: {
  label: string;
  value: number | string;
  color: string;
  urgent?: boolean;
}) {
  return (
    <div className={cn(
      "rounded-xl bg-white p-4 shadow-sm border",
      urgent ? "border-amber-300 ring-2 ring-amber-200" : "border-gray-200"
    )}>
      <p className="text-xs font-medium text-gray-500">{label}</p>
      <p className={cn(
        "mt-1 text-2xl font-bold",
        urgent ? "text-amber-600" : "text-gray-900"
      )}>
        {value}
      </p>
      <div className={cn("mt-2 h-1 w-8 rounded-full", color)} />
    </div>
  );
}

function StatRow({
  label,
  value,
  good,
  bad,
}: {
  label: string;
  value: number | string;
  good?: boolean;
  bad?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={cn(
        "text-sm font-semibold",
        good ? "text-green-600" : bad ? "text-red-500" : "text-gray-900"
      )}>
        {value}
      </span>
    </div>
  );
}

function AppointmentList({
  items,
  emptyMessage,
}: {
  items: AppointmentDetail[];
  emptyMessage: string;
}) {
  if (items.length === 0) {
    return <p className="text-sm text-gray-400 py-4 text-center">{emptyMessage}</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((appt) => (
        <div
          key={appt.id}
          className="flex items-center gap-4 rounded-lg border border-gray-100 p-4 hover:bg-gray-50 transition-colors"
        >
          {/* Time block */}
          <div className="flex-shrink-0 text-center w-16">
            <p className="text-lg font-bold text-gray-900">
              {new Date(appt.scheduled_start).toLocaleTimeString("en-US", {
                hour: "numeric",
                minute: "2-digit",
              })}
            </p>
            <p className="text-xs text-gray-400">
              {formatDate(appt.scheduled_start)}
            </p>
          </div>

          {/* Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <Link
                href={`/leads/${appt.lead_id}`}
                className="text-sm font-semibold text-gray-900 hover:text-solar-600"
              >
                {appt.lead_name}
              </Link>
              <span className={cn(
                "rounded-full px-2 py-0.5 text-xs font-medium",
                apptStatusBadge(appt.status)
              )}>
                {appt.status.replace(/_/g, " ")}
              </span>
              {appt.lead_score != null && (
                <span className={cn("text-xs font-semibold", scoreColor(appt.lead_score))}>
                  Score: {appt.lead_score}
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 mt-1">
              {appt.address && (
                <span className="text-xs text-gray-500 truncate max-w-[200px]">
                  {appt.address}
                </span>
              )}
              {appt.lead_phone && (
                <span className="text-xs text-gray-400">{appt.lead_phone}</span>
              )}
            </div>
            {appt.notes && (
              <p className="text-xs text-gray-400 mt-1 truncate">{appt.notes}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
