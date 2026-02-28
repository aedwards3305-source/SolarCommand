import type { Metadata } from "next";
import Link from "next/link";
import PageHero from "@/components/portal/PageHero";
import CtaBreak from "@/components/portal/CtaBreak";

export const metadata: Metadata = {
  title: "Solar Savings & Maryland Tax Credits | Solar Command",
  description:
    "Discover how much you can save with solar in Maryland. 30% federal tax credit, 6% state sales tax exemption, and county property tax credits up to $5,000.",
};

export default function SolarSavingsPage() {
  return (
    <div>
      {/* ── Hero ──────────────────────────────────────────────── */}
      <PageHero
        title="Solar Savings"
        subtitle="Save Money While Saving the Planet"
        description="A quality solar system reduces your electric bill by 50 to 90 percent. Maryland offers some of the best solar incentives in the country."
      />

      {/* ── Section 1: Why Purchase Solar Panels ──────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="grid items-center gap-10 lg:grid-cols-2">
            {/* Text */}
            <div>
              <h2 className="text-4xl font-bold text-amber-600">
                Why Purchase Solar Panels?
              </h2>
              <p className="mt-4 text-solar-700 leading-relaxed">
                Solar energy is one of the fastest-growing industries in the
                United States, with 42% annual growth over the past decade. The
                reason is simple: costs have dropped dramatically while utility
                prices keep climbing.
              </p>
              <p className="mt-4 text-solar-700 leading-relaxed">
                Over the past decade, residential solar costs have decreased by
                50%, while utility electricity prices have risen 16%. A quality
                solar PV system reduces your electric bill by 50 to 90 percent,
                locking in predictable energy costs for 25 years or more.
              </p>
              <p className="mt-4 text-solar-700 leading-relaxed">
                With $0 down financing, the 30% federal tax credit, and
                Maryland&apos;s generous state incentives, there has never been a
                better time to invest in solar energy for your home.
              </p>
            </div>

            {/* Stat Cards */}
            <div className="grid gap-4 sm:grid-cols-1">
              <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 text-center">
                <p className="text-4xl font-extrabold text-green-500">50%</p>
                <p className="mt-2 text-base font-medium text-solar-700">
                  Cost Decrease Over Last Decade
                </p>
              </div>
              <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 text-center">
                <p className="text-4xl font-extrabold text-red-500">16%</p>
                <p className="mt-2 text-base font-medium text-solar-700">
                  Utility Price Increase
                </p>
              </div>
              <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 text-center">
                <p className="text-4xl font-extrabold text-solar-500">
                  50-90%
                </p>
                <p className="mt-2 text-base font-medium text-solar-700">
                  Electric Bill Reduction
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 2: Maryland Solar Incentives ──────────────── */}
      <section className="bg-white border-t border-gray-100 py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-amber-600">
              Maryland Solar Incentives
            </h2>
            <p className="mt-2 text-solar-700">
              Maryland homeowners benefit from multiple solar incentives
            </p>
          </div>

          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {/* 30% Federal Tax Credit */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-600">
                  <svg
                    width={28}
                    height={28}
                    className="h-7 w-7"
                    fill="none"
                    viewBox="0 0 24 24"
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
                  <h3 className="text-xl font-semibold text-amber-600">
                    30% Federal Tax Credit (ITC)
                  </h3>
                  <p className="mt-3 text-4xl font-extrabold text-green-500">
                    30%
                  </p>
                  <p className="mt-3 text-base text-solar-700 leading-relaxed">
                    Deduct 30% of the cost of your solar system from your federal
                    income taxes. Available through 2032.
                  </p>
                </div>
              </div>
            </div>

            {/* 6% State Sales Tax Exemption */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-solar-100 text-solar-600">
                  <svg
                    width={28}
                    height={28}
                    className="h-7 w-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M9 14.25l6-6m4.5-3.493V21.75l-3.75-1.5-3.75 1.5-3.75-1.5-3.75 1.5V4.757c0-1.108.806-2.057 1.907-2.185a48.507 48.507 0 0111.186 0c1.1.128 1.907 1.077 1.907 2.185zM9.75 9h.008v.008H9.75V9zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm4.125 4.5h.008v.008h-.008V13.5zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-amber-600">
                    6% State Sales Tax Exemption
                  </h3>
                  <p className="mt-3 text-base text-solar-700 leading-relaxed">
                    Maryland exempts solar installations from the state&apos;s 6%
                    sales tax. On a $15,000 system, that&apos;s $900 in savings.
                  </p>
                </div>
              </div>
            </div>

            {/* County Property Tax Credits */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-600">
                  <svg
                    width={28}
                    height={28}
                    className="h-7 w-7"
                    fill="none"
                    viewBox="0 0 24 24"
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
                  <h3 className="text-xl font-semibold text-amber-600">
                    County Property Tax Credits
                  </h3>
                  <ul className="mt-3 space-y-2">
                    <li className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2.5 text-base">
                      <span className="text-solar-700">Baltimore County</span>
                      <span className="font-semibold text-amber-600">
                        up to $5,000
                      </span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2.5 text-base">
                      <span className="text-solar-700">
                        Prince George&apos;s County
                      </span>
                      <span className="font-semibold text-amber-600">
                        up to $5,000
                      </span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2.5 text-base">
                      <span className="text-solar-700">
                        Anne Arundel County
                      </span>
                      <span className="font-semibold text-amber-600">
                        up to $2,500
                      </span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2.5 text-base">
                      <span className="text-solar-700">Harford County</span>
                      <span className="font-semibold text-amber-600">
                        up to $2,500
                      </span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Net Metering */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl bg-sunburst-100 text-sunburst-600">
                  <svg
                    width={28}
                    height={28}
                    className="h-7 w-7"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={1.5}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"
                    />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-amber-600">
                    Net Metering
                  </h3>
                  <p className="mt-3 text-base text-solar-700 leading-relaxed">
                    Excess solar energy gets credited back to you by your utility
                    company. Your meter runs backward when you produce more than
                    you use.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 3: How Solar Saves You Money ──────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600">
            How Solar Saves You Money
          </h2>
          <div className="mt-10 grid gap-8 sm:grid-cols-3">
            {/* Reduce Your Electric Bill */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg
                  width={28}
                  height={28}
                  className="h-7 w-7"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-xl font-semibold text-amber-600">
                Reduce Your Electric Bill
              </h3>
              <p className="mt-2 text-base text-solar-700 leading-relaxed">
                With solar, you lock in a fixed monthly payment that replaces
                your fluctuating utility bill. While utility rates continue to
                rise year after year, your solar payment stays the same for the
                life of the system.
              </p>
            </div>

            {/* Earn Net Metering Credits */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-green-100 text-green-600">
                <svg
                  width={28}
                  height={28}
                  className="h-7 w-7"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"
                  />
                </svg>
              </div>
              <h3 className="mt-4 text-xl font-semibold text-amber-600">
                Earn Net Metering Credits
              </h3>
              <p className="mt-2 text-base text-solar-700 leading-relaxed">
                When your solar panels produce more electricity than you use, the
                excess energy is sent to the grid and credited to your account by
                your utility company. Those credits offset the electricity you
                draw at night or on cloudy days.
              </p>
            </div>

            {/* Increase Your Home Value */}
            <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200 text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-sunburst-100 text-sunburst-600">
                <svg
                  width={28}
                  height={28}
                  className="h-7 w-7"
                  fill="none"
                  viewBox="0 0 24 24"
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
              <h3 className="mt-4 text-xl font-semibold text-amber-600">
                Increase Your Home Value
              </h3>
              <p className="mt-2 text-base text-solar-700 leading-relaxed">
                Studies show that solar panels add an average of $15,000 to a
                home&apos;s resale value. Buyers are willing to pay more for a
                home with lower energy costs and a clean energy system already in
                place.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 4: Bill Audit Service ──────────────────────── */}
      <section className="bg-solar-900 py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-500/20">
            <svg
              width={28}
              height={28}
              className="h-7 w-7 text-solar-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-4xl font-bold text-white sm:text-5xl">
            Already Overpaying Your Electric Bill?
          </h2>
          <p className="mt-4 text-xl text-gray-300 leading-relaxed">
            We review your last 36 months of electricity bills to find
            overcharges and billing errors. Many Maryland homeowners have
            overpaid their utility company without knowing it — we help you
            recover that money.
          </p>
          <div className="mt-8">
            <Link
              href="/solar/get-quote"
              className="inline-flex items-center gap-2 rounded-full bg-solar-500 px-8 py-3 text-lg font-bold text-white shadow-lg hover:bg-solar-600 transition-colors"
            >
              Get Your Free Bill Audit
              <svg
                width={20}
                height={20}
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
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
        </div>
      </section>

      {/* ── CTA Break ─────────────────────────────────────────── */}
      <CtaBreak />
    </div>
  );
}
