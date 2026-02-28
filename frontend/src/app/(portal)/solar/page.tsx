import type { Metadata } from "next";
import Link from "next/link";
import CtaBreak from "@/components/portal/CtaBreak";

export const metadata: Metadata = {
  title: "Solar Command | Premium Solar Panels for Maryland Homes",
  description:
    "Solar Command installs premium Sunburst Solar systems in Maryland. 25-year warranty, Enphase battery backup, $0 down financing. MHIC #165263.",
};

export default function SolarHomePage() {
  return (
    <div>
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-solar-600 via-solar-700 to-solar-800 text-white">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute -top-40 -right-40 h-[500px] w-[500px] rounded-full bg-solar-400 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-[300px] w-[300px] rounded-full bg-fuchsia-400 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-5xl px-4 py-16 text-center sm:px-6 sm:py-24">
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-8xl">
            Achieve Energy Independence
          </h1>
          <p className="mt-4 text-xl font-medium text-solar-200 sm:text-2xl lg:text-3xl">
            Meeting the Highest Standards in the Solar System
          </p>
          <p className="mx-auto mt-5 max-w-2xl text-xl text-solar-100 sm:text-2xl leading-relaxed">
            Solar Command installs premium Sunburst Solar systems with a
            comprehensive 25-year warranty, Enphase battery backup, and $0
            down financing — proudly serving Maryland.
          </p>
          <div className="mt-10 flex flex-wrap gap-4 justify-center">
            <Link
              href="/solar/get-quote"
              className="inline-flex items-center gap-2 rounded-full bg-white px-10 py-4 text-xl font-bold text-solar-700 shadow-lg hover:bg-solar-50 transition-colors"
            >
              Schedule an Appointment
            </Link>
            <Link
              href="/solar/why-solar-command"
              className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-9 py-4 text-xl font-semibold backdrop-blur-sm hover:bg-white/20 transition-colors"
            >
              Learn More
            </Link>
          </div>
          {/* Trust badges */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            {[
              "25-Year Warranty",
              "Authorized Sunburst Solar Dealer",
              "Sponsored by Sunrun",
              "MHIC Licensed",
            ].map((badge) => (
              <span
                key={badge}
                className="rounded-full border border-white/30 bg-white/10 px-5 py-2 text-base font-medium backdrop-blur-sm"
              >
                {badge}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Hero Image ─────────────────────────────────────── */}
      <section className="bg-white py-10 sm:py-14">
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          <div className="overflow-hidden rounded-2xl shadow-2xl">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/commercial-hero.png"
              alt="Solar Command commercial solar panel installation"
              width={908}
              height={592}
              className="h-auto w-full object-cover"
            />
          </div>
        </div>
      </section>

      {/* ── Make the Smart Investment ────────────────────────── */}
      <section className="bg-white py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600 sm:text-5xl">
            Make the Smart Investment: Go Solar!
          </h2>
          <div className="mt-12 grid gap-8 sm:grid-cols-3">
            {[
              {
                icon: "M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941",
                title: "Utility Costs Are Rising",
                desc: "Utility prices increased 16% over the past decade, while residential solar costs dropped 50%. Lock in your savings now.",
              },
              {
                icon: "M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21",
                title: "Increase Home Value",
                desc: "Solar panels increase your home's resale value by an average of $15,000.",
              },
              {
                icon: "M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
                title: "Federal Tax Credit",
                desc: "The federal government offers a 30% tax credit to homeowners who switch to solar — available through 2032.",
              },
            ].map((item) => (
              <div
                key={item.title}
                className="rounded-xl bg-white p-8 text-center shadow-sm border border-gray-200"
              >
                <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                  <svg width={40} height={40} className="h-10 w-10" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                  </svg>
                </div>
                <h3 className="mt-5 text-2xl font-semibold text-amber-600">
                  {item.title}
                </h3>
                <p className="mt-3 text-lg text-solar-800 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Explore Our Services ─────────────────────────────── */}
      <section className="bg-white py-16 sm:py-20 border-t border-gray-100">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="text-center text-4xl font-bold text-amber-600 sm:text-5xl">
            Explore Our Services
          </h2>
          <p className="mt-3 text-center text-xl text-solar-700 sm:text-2xl">
            Discover what Solar Command can do for your Maryland home
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2">
            {[
              {
                href: "/solar/why-solar-command",
                title: "Why Solar Command",
                desc: "Our 6 differentiators, 25-year warranty, certified installation, and the 6-step process from proposal to activation.",
                icon: "M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z",
                accent: "bg-solar-100 text-solar-600",
              },
              {
                href: "/solar/savings",
                title: "Solar Savings",
                desc: "Maryland incentives including the 30% federal tax credit, state sales tax exemption, and county property tax credits.",
                icon: "M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
                accent: "bg-green-100 text-green-600",
              },
              {
                href: "/solar/batteries",
                title: "Battery Storage",
                desc: "Enphase IQ battery backup systems — store excess energy for nighttime, cloudy days, and power outages.",
                icon: "M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z",
                accent: "bg-sunburst-100 text-sunburst-600",
              },
              {
                href: "/solar/financing",
                title: "Financing Options",
                desc: "$0 down financing, leasing, PPAs, and lease-to-own plans. Flexible payment solutions for every budget.",
                icon: "M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z",
                accent: "bg-purple-100 text-purple-600",
              },
            ].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group flex gap-5 rounded-xl bg-white p-8 shadow-sm border border-gray-200 hover:shadow-md hover:border-solar-300 transition-all"
              >
                <div className={`flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl ${item.accent}`}>
                  <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-amber-600 group-hover:text-solar-600 transition-colors sm:text-2xl">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-lg text-solar-800 leading-relaxed">
                    {item.desc}
                  </p>
                  <span className="mt-3 inline-flex items-center gap-1.5 text-lg font-medium text-solar-600">
                    Learn more
                    <svg width={18} height={18} className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <CtaBreak />
    </div>
  );
}
