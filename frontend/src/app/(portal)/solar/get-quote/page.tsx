"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { portalApi } from "@/lib/api/portal";

export default function GetQuotePage() {
  const router = useRouter();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    address: "",
    city: "",
    state: "MD",
    zip_code: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const res = await portalApi.submitQuote(form);
      if (res.token) {
        router.push(`/p/${res.token}`);
      } else {
        router.push("/solar/thank-you");
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const updateField = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div>
      {/* ── 1. Hero Header ───────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-solar-600 via-solar-700 to-solar-800 text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-40 -right-40 h-[500px] w-[500px] rounded-full bg-solar-400 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-[300px] w-[300px] rounded-full bg-fuchsia-400 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-3xl px-4 py-16 text-center sm:px-6 sm:py-20">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Get Your Free Solar Quote
          </h1>
          <p className="mt-4 text-lg text-solar-100 sm:text-xl">
            No obligation. No pressure. Just honest solar savings numbers.
          </p>
        </div>
      </section>

      {/* ── 2. Trust Signals ─────────────────────────────────── */}
      <section className="border-b border-gray-100 bg-white py-5">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-center gap-3 px-4 sm:px-6">
          {/* 25-Year Warranty */}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3.5 py-1.5 text-xs font-medium text-solar-700">
            <svg
              width={14}
              height={14}
              className="h-3.5 w-3.5 text-solar-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
              />
            </svg>
            25-Year Warranty
          </span>

          {/* Authorized Dealer */}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3.5 py-1.5 text-xs font-medium text-solar-700">
            <svg
              width={14}
              height={14}
              className="h-3.5 w-3.5 text-solar-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"
              />
            </svg>
            Authorized Sunburst Solar Dealer
          </span>

          {/* MHIC License */}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3.5 py-1.5 text-xs font-medium text-solar-700">
            <svg
              width={14}
              height={14}
              className="h-3.5 w-3.5 text-solar-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 9h3.75M15 12h3.75M15 15h3.75M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5zm6-10.125a1.875 1.875 0 11-3.75 0 1.875 1.875 0 013.75 0zm1.294 6.336a6.721 6.721 0 01-3.17.789 6.721 6.721 0 01-3.168-.789 3.376 3.376 0 016.338 0z"
              />
            </svg>
            MHIC #165263
          </span>

          {/* $0 Down */}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3.5 py-1.5 text-xs font-medium text-solar-700">
            <svg
              width={14}
              height={14}
              className="h-3.5 w-3.5 text-solar-600"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            $0 Down Options
          </span>
        </div>
      </section>

      {/* ── 3. Quote Form ────────────────────────────────────── */}
      <section className="py-12 sm:py-16">
        <div className="mx-auto max-w-2xl px-4 sm:px-6">
          <div className="rounded-2xl bg-white p-6 shadow-lg border border-gray-200 sm:p-8">
            {error && (
              <div className="mb-5 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700 flex items-start gap-2">
                <svg
                  width={18}
                  height={18}
                  className="mt-0.5 h-[18px] w-[18px] flex-shrink-0 text-red-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
                  />
                </svg>
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              {/* First Name + Last Name */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    First Name
                  </label>
                  <input
                    type="text"
                    required
                    value={form.first_name}
                    onChange={(e) => updateField("first_name", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    Last Name
                  </label>
                  <input
                    type="text"
                    required
                    value={form.last_name}
                    onChange={(e) => updateField("last_name", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                    placeholder="Smith"
                  />
                </div>
              </div>

              {/* Phone + Email */}
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    Phone
                  </label>
                  <input
                    type="tel"
                    required
                    value={form.phone}
                    onChange={(e) => updateField("phone", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                    placeholder="(555) 123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={form.email}
                    onChange={(e) => updateField("email", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                    placeholder="john@example.com"
                  />
                </div>
              </div>

              {/* Street Address */}
              <div className="mt-4">
                <label className="block text-sm font-medium text-solar-700 mb-1">
                  Street Address
                </label>
                <input
                  type="text"
                  required
                  value={form.address}
                  onChange={(e) => updateField("address", e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                  placeholder="123 Main Street"
                />
              </div>

              {/* City + State + Zip Code */}
              <div className="mt-4 grid gap-4 sm:grid-cols-3">
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    required
                    value={form.city}
                    onChange={(e) => updateField("city", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                    placeholder="Baltimore"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    State
                  </label>
                  <input
                    type="text"
                    readOnly
                    value="Maryland"
                    tabIndex={-1}
                    className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2.5 text-sm text-gray-600 cursor-not-allowed outline-none"
                  />
                  <input type="hidden" name="state" value="MD" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-solar-700 mb-1">
                    Zip Code
                  </label>
                  <input
                    type="text"
                    required
                    value={form.zip_code}
                    onChange={(e) => updateField("zip_code", e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2.5 text-sm focus:ring-2 focus:ring-solar-500 focus:border-solar-500 outline-none"
                    placeholder="21201"
                  />
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={submitting}
                className="mt-6 w-full rounded-lg bg-solar-600 px-6 py-3 text-base font-bold text-white hover:bg-solar-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? "Submitting..." : "Get My Free Quote"}
              </button>

              {/* Consent */}
              <p className="mt-3 text-center text-xs text-gray-400">
                By submitting, you consent to receive calls and texts about your
                solar quote. No purchase required. MHIC #165263.
              </p>
            </form>
          </div>
        </div>
      </section>

      {/* ── 4. Why Solar Command? ──────────────────────────────── */}
      <section className="pb-16 sm:pb-20">
        <div className="mx-auto max-w-2xl px-4 sm:px-6">
          <div className="rounded-xl bg-solar-50 border border-solar-200 p-6 text-center">
            <p className="text-base font-semibold text-amber-600">
              Want to learn more first?
            </p>
            <p className="mt-1 text-sm text-solar-700">
              Discover our 25-year warranty, certified installers, and the 6-step process.
            </p>
            <a
              href="/solar/why-solar-command"
              className="mt-4 inline-flex items-center gap-2 rounded-full bg-solar-600 px-6 py-2.5 text-sm font-bold text-white hover:bg-solar-700 transition-colors"
            >
              Why Solar Command
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
