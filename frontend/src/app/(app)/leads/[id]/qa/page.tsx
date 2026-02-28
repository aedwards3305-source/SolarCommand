"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { cn, formatDateTime } from "@/lib/utils";

interface QAReview {
  id: number;
  lead_id: number;
  conversation_id: number | null;
  compliance_score: number;
  flags: Array<{ flag: string; severity: string; evidence?: string }> | null;
  checklist_pass: boolean;
  rationale: string | null;
  reviewed_by: string;
  created_at: string;
}

export default function LeadQAPage() {
  const params = useParams();
  const leadId = Number(params.id);
  const [reviews, setReviews] = useState<QAReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getLeadQA(leadId)
      .then(setReviews)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load QA"))
      .finally(() => setLoading(false));
  }, [leadId]);

  const scoreColor = (score: number) => {
    if (score >= 80) return "text-green-700 bg-green-50";
    if (score >= 60) return "text-yellow-700 bg-yellow-50";
    return "text-red-700 bg-red-50";
  };

  const severityColor = (severity: string) => {
    if (severity === "critical") return "bg-red-100 text-red-800";
    if (severity === "warning") return "bg-yellow-100 text-yellow-800";
    return "bg-blue-100 text-blue-800";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link href={`/leads/${leadId}`} className="text-sm text-gray-500 hover:text-gray-700">
          &larr; Back to lead
        </Link>
        <h1 className="text-xl font-bold text-gray-900">QA Reviews</h1>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="animate-pulse text-gray-400">Loading QA reviews...</div>
      ) : reviews.length === 0 ? (
        <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center text-gray-400">
          No QA reviews yet. QA reviews are generated automatically when conversations are processed.
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((r) => (
            <div key={r.id} className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-4 flex items-center justify-between border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className={cn("rounded-lg px-3 py-1.5 text-lg font-bold", scoreColor(r.compliance_score))}>
                    {r.compliance_score}/100
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        r.checklist_pass ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                      )}>
                        {r.checklist_pass ? "PASS" : "FAIL"}
                      </span>
                      <span className="text-xs text-gray-500">
                        Reviewed by: {r.reviewed_by}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">{formatDateTime(r.created_at)}</p>
                  </div>
                </div>
              </div>

              {/* Rationale */}
              {r.rationale && (
                <div className="px-4 py-3 bg-gray-50">
                  <p className="text-sm text-gray-700">{r.rationale}</p>
                </div>
              )}

              {/* Flags */}
              {r.flags && r.flags.length > 0 && (
                <div className="px-4 py-3 space-y-2">
                  <p className="text-xs font-semibold text-gray-500 uppercase">Flags</p>
                  {r.flags.map((f, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium shrink-0", severityColor(f.severity))}>
                        {f.severity}
                      </span>
                      <div>
                        <p className="text-sm text-gray-700">{f.flag}</p>
                        {f.evidence && (
                          <p className="text-xs text-gray-500 mt-0.5 italic">"{f.evidence}"</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
