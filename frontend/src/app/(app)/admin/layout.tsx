"use client";

import { usePathname } from "next/navigation";

const PAGE_META: Record<string, { title: string; description: string }> = {
  "/admin/qa": {
    title: "QA Reviews",
    description: "Review compliance scores, flags, and checklist results",
  },
  "/admin/experiments": {
    title: "Experiments",
    description: "A/B test results for script variants across channels",
  },
  "/admin/audit": {
    title: "Audit Log",
    description: "Complete trail of system actions and data changes",
  },
  "/admin/scripts": {
    title: "Scripts",
    description: "Manage call scripts, versions, and channel assignments",
  },
  "/admin/ai-runs": {
    title: "AI Operator Runs",
    description: "Monitor AI task execution, latency, and costs",
  },
  "/admin/cost-center": {
    title: "Cost Center",
    description: "Monthly breakdown of AI and voice call spending",
  },
  "/admin/source-health": {
    title: "Source Health",
    description: "Uptime, ingestion volumes, and error monitoring",
  },
  "/admin/sources": {
    title: "Data Sources",
    description: "Configure and monitor lead discovery data sources",
  },
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const meta = PAGE_META[pathname] ?? null;

  return (
    <div className="min-h-[calc(100vh-3rem)]">
      {/* Accent bar */}
      <div className="h-1 bg-gradient-to-r from-solar-600 via-solar-400 to-sunburst-400 rounded-full mb-6" />

      {/* Page header */}
      {meta && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-widest text-solar-500">
              Admin
            </span>
            <span className="text-gray-300">/</span>
            <span className="text-[10px] font-medium uppercase tracking-wide text-gray-400">
              {meta.title}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">
            {meta.title}
          </h1>
          <p className="mt-1 text-sm text-gray-500">{meta.description}</p>
        </div>
      )}

      {children}
    </div>
  );
}
