import type { Metadata } from "next";
import Link from "next/link";
import PageHero from "@/components/portal/PageHero";
import CtaBreak from "@/components/portal/CtaBreak";

export const metadata: Metadata = {
  title: "Solar Financing Options | $0 Down | Solar Command",
  description:
    "Flexible solar financing and leasing options for Maryland homeowners. $0 down, competitive rates, and multiple payment plans available.",
};

const FINANCING_BENEFITS = [
  "Largest long-term savings",
  "Home value increases",
  "Federal tax credit applies",
  "Full system ownership",
  "25-year warranty protection",
];

const LEASING_BENEFITS = [
  "No money down",
  "Immediate bill savings",
  "Maintenance included",
  "Easy and hassle-free",
  "Flexible terms available",
];

const FINANCING_TYPES = [
  {
    title: "Secured Loans",
    description:
      "Use your home as collateral for lower interest rates and longer terms. Ideal for homeowners with equity.",
  },
  {
    title: "Unsecured Loans",
    description:
      "No collateral required. Higher rates but simpler approval process. Good credit recommended.",
  },
  {
    title: "Power Purchase Agreements (PPAs)",
    description:
      "We install the system, you buy the power at a fixed rate lower than your utility. No ownership hassle.",
  },
  {
    title: "Lease-to-Own",
    description:
      "Start with lease payments and transition to full ownership over time. Combine flexibility with long-term value.",
  },
];

const PAYMENT_PLANS = [
  {
    title: "Monthly Lease",
    description:
      "Low monthly payments with maintenance included. Start saving immediately with no upfront investment.",
  },
  {
    title: "Prepaid Lease",
    description:
      "Pay upfront for the full lease term. Maximize your long-term savings with a single payment.",
  },
  {
    title: "System Purchase",
    description:
      "Own your system outright and enjoy the maximum financial benefits including tax credits and home value increase.",
  },
];

const WARRANTY_ROWS = [
  { feature: "Complete System Coverage", sunburst: true, industry: false },
  { feature: "Part Removal & Replacement", sunburst: true, industry: false },
  { feature: "Shipping Included", sunburst: true, industry: false },
  {
    feature: "25-Year Product Warranty",
    sunburst: true,
    industry: "10-12 Years",
  },
  { feature: "Production Guarantee", sunburst: true, industry: false },
];

export default function SolarFinancingPage() {
  return (
    <div>
      {/* Hero */}
      <PageHero
        title="Solar Financing"
        subtitle="Flexible Payment Solutions for Every Budget"
        description="Going solar is more affordable than you think. With $0 down options and flexible financing, your monthly solar payment can be less than your current electric bill."
      />

      {/* ── Section 1: Financing vs Leasing ────────────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600">
            Financing vs. Leasing
          </h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-2">
            {/* Financing Card */}
            <div className="rounded-xl border border-gray-200 border-t-4 border-t-solar-500 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                  <svg
                    width={28}
                    height={28}
                    viewBox="0 0 24 24"
                    fill="none"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-amber-600">Financing</h3>
                  <p className="text-base font-medium text-solar-600">
                    Own Your System
                  </p>
                </div>
              </div>
              <ul className="mt-5 space-y-3">
                {FINANCING_BENEFITS.map((benefit) => (
                  <li key={benefit} className="flex items-start gap-2.5">
                    <svg
                      width={20}
                      height={20}
                      viewBox="0 0 24 24"
                      fill="none"
                      className="mt-0.5 flex-shrink-0 text-solar-600"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <span className="text-base text-solar-700">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Leasing Card */}
            <div className="rounded-xl border border-gray-200 border-t-4 border-t-sunburst-500 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-sunburst-100 text-sunburst-600">
                  <svg
                    width={28}
                    height={28}
                    viewBox="0 0 24 24"
                    fill="none"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-amber-600">Leasing</h3>
                  <p className="text-base font-medium text-sunburst-600">
                    No Upfront Cost
                  </p>
                </div>
              </div>
              <ul className="mt-5 space-y-3">
                {LEASING_BENEFITS.map((benefit) => (
                  <li key={benefit} className="flex items-start gap-2.5">
                    <svg
                      width={20}
                      height={20}
                      viewBox="0 0 24 24"
                      fill="none"
                      className="mt-0.5 flex-shrink-0 text-sunburst-600"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <span className="text-base text-solar-700">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 2: Types of Solar Financing ────────────────── */}
      <section className="bg-white border-t border-gray-100 py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600">
            Types of Solar Financing &amp; Leasing
          </h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {FINANCING_TYPES.map((item) => (
              <div
                key={item.title}
                className="rounded-xl bg-white p-6 shadow-sm border border-gray-200"
              >
                <h3 className="text-xl font-semibold text-amber-600">
                  {item.title}
                </h3>
                <p className="mt-2 text-base text-solar-700 leading-relaxed">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 3: $0 Down Callout ─────────────────────────── */}
      <section className="bg-gradient-to-r from-solar-600 to-solar-700 py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <p className="text-6xl font-extrabold text-white sm:text-7xl">
            $0 Down to Get Started
          </p>
          <p className="mx-auto mt-4 max-w-2xl text-xl text-solar-100 leading-relaxed">
            Pay as little as zero down with no out-of-pocket costs for up to 60
            days after installation. Your price is guaranteed in writing for 60
            days.
          </p>
          <p className="mt-4 text-base font-medium text-solar-200">
            Backed by Blackstone and Truist, a multi-billion dollar financial
            institution.
          </p>
        </div>
      </section>

      {/* ── Section 4: Payment Plans ───────────────────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600">
            Choose Your Plan
          </h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {PAYMENT_PLANS.map((plan) => (
              <div
                key={plan.title}
                className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 flex flex-col"
              >
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                  <svg
                    width={28}
                    height={28}
                    viewBox="0 0 24 24"
                    fill="none"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z"
                    />
                  </svg>
                </div>
                <h3 className="mt-4 text-xl font-semibold text-amber-600">
                  {plan.title}
                </h3>
                <p className="mt-2 flex-1 text-base text-solar-700 leading-relaxed">
                  {plan.description}
                </p>
                <Link
                  href="/solar/get-quote"
                  className="mt-5 inline-flex items-center gap-1 text-base font-semibold text-solar-600 hover:text-solar-700 transition-colors"
                >
                  Learn More
                  <svg
                    width={16}
                    height={16}
                    viewBox="0 0 24 24"
                    fill="none"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
                    />
                  </svg>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 5: Warranty Comparison ─────────────────────── */}
      <section className="bg-white border-t border-gray-100 py-16 sm:py-20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600">
            Sunburst Solar Complete Confidence Warranty
          </h2>
          <div className="mt-10 overflow-hidden rounded-xl bg-white shadow-sm border border-gray-200">
            {/* Table Header */}
            <div className="grid grid-cols-3 border-b border-gray-200 bg-gray-50 px-6 py-4">
              <p className="text-base font-semibold text-amber-600">Feature</p>
              <p className="text-center text-base font-semibold text-solar-700">
                Sunburst Solar
              </p>
              <p className="text-center text-base font-semibold text-solar-700">
                Industry Standard
              </p>
            </div>
            {/* Table Rows */}
            {WARRANTY_ROWS.map((row, i) => (
              <div
                key={row.feature}
                className={`grid grid-cols-3 items-center px-6 py-4 ${
                  i < WARRANTY_ROWS.length - 1
                    ? "border-b border-gray-100"
                    : ""
                }`}
              >
                <p className="text-base font-medium text-solar-800">
                  {row.feature}
                </p>
                <div className="flex justify-center">
                  {row.sunburst === true ? (
                    <svg
                      width={24}
                      height={24}
                      viewBox="0 0 24 24"
                      fill="none"
                      className="text-green-600"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  ) : (
                    <span className="text-base font-medium text-green-600">
                      {String(row.sunburst)}
                    </span>
                  )}
                </div>
                <div className="flex justify-center">
                  {row.industry === false ? (
                    <svg
                      width={24}
                      height={24}
                      viewBox="0 0 24 24"
                      fill="none"
                      className="text-red-500"
                      strokeWidth={2}
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                  ) : (
                    <span className="text-base font-medium text-solar-700">
                      {String(row.industry)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Break ──────────────────────────────────────────── */}
      <CtaBreak
        heading="Start Saving with $0 Down"
        subtext="Get your free quote and explore financing options that work for your budget."
      />
    </div>
  );
}
