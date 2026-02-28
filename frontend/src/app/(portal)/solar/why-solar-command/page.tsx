import type { Metadata } from "next";
import PageHero from "@/components/portal/PageHero";
import CtaBreak from "@/components/portal/CtaBreak";

export const metadata: Metadata = {
  title: "Why Solar Command | Maryland's Trusted Solar Installer",
  description:
    "Discover why Solar Command is Maryland's top choice for Sunburst Solar panel installation. 25-year warranty, certified installers, MHIC #165263.",
};

export default function WhySolarCommandPage() {
  return (
    <div>
      {/* ── Hero ────────────────────────────────────────────── */}
      <PageHero
        title="Why Solar Command"
        subtitle="Meeting the Highest Standards in the Solar System"
        description="Solar Command is your one-stop shop for high-quality Sunburst Solar panels and battery backup systems. From consultation to after-sales service, we do it all."
      />

      {/* ── Section 1: 6 Differentiator Cards ───────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {/* Premium Products */}
            <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-200">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-amber-600">Premium Products</h3>
              <p className="mt-2 text-sm text-solar-700 leading-relaxed">
                Components manufactured by industry leaders, rigorously tested and backed by a 25-year warranty.
              </p>
            </div>

            {/* Certified Installation */}
            <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-200">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 00-.491 6.347A48.62 48.62 0 0112 20.904a48.62 48.62 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.906 59.906 0 0112 3.493a59.903 59.903 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-amber-600">Certified Installation</h3>
              <p className="mt-2 text-sm text-solar-700 leading-relaxed">
                Licensed, bonded, and insured installers with an average of 10+ years of experience in Maryland.
              </p>
            </div>

            {/* Attention to Detail */}
            <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-200">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-amber-600">Attention to Detail</h3>
              <p className="mt-2 text-sm text-solar-700 leading-relaxed">
                Every system gets a 20-point pre-installation inspection and a 25-point post-installation inspection.
              </p>
            </div>

            {/* Expert Advice */}
            <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-200">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-amber-600">Expert Advice</h3>
              <p className="mt-2 text-sm text-solar-700 leading-relaxed">
                We research every product option so you don&apos;t have to. Consultations tailored to your unique energy needs.
              </p>
            </div>

            {/* Hassle-Free Pricing */}
            <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-200">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-amber-600">Hassle-Free Pricing</h3>
              <p className="mt-2 text-sm text-solar-700 leading-relaxed">
                Transparent quotes based on satellite imagery and your electricity usage. Price guaranteed in writing for 60 days.
              </p>
            </div>

            {/* Flexible Payment */}
            <div className="rounded-xl bg-white p-6 text-center shadow-sm border border-gray-200">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-solar-100 text-solar-600">
                <svg width={28} height={28} className="h-7 w-7" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-amber-600">Flexible Payment</h3>
              <p className="mt-2 text-sm text-solar-700 leading-relaxed">
                Pay as little as $0 down. No out-of-pocket costs for up to 60 days after installation. Backed by Blackstone and Truist.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 2: Warranty Comparison ──────────────────── */}
      <section className="bg-white border-t border-gray-100 py-16 sm:py-20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          <h2 className="text-center text-3xl font-bold text-amber-600">
            Sunburst Solar Complete Confidence Warranty
          </h2>
          <p className="mt-2 text-center text-solar-700">
            Our 25-year warranty leaves the industry standard in the shade
          </p>

          <div className="mt-10 overflow-hidden rounded-xl bg-white shadow-sm border border-gray-200">
            {/* Table Header */}
            <div className="grid grid-cols-3 bg-gray-50 border-b border-gray-200">
              <div className="px-5 py-4 text-sm font-semibold text-gray-700">Coverage</div>
              <div className="px-5 py-4 text-center text-sm font-semibold text-solar-700 bg-solar-50">
                Sunburst Solar (25 Years)
              </div>
              <div className="px-5 py-4 text-center text-sm font-semibold text-solar-700">
                Industry Standard (10-12 Years)
              </div>
            </div>

            {/* Row: Complete System Coverage */}
            <div className="grid grid-cols-3 border-b border-gray-100">
              <div className="px-5 py-3.5 text-sm text-gray-700">Complete System Coverage</div>
              <div className="px-5 py-3.5 text-center bg-solar-50/40">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div className="px-5 py-3.5 text-center">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>

            {/* Row: Defective Part Removal */}
            <div className="grid grid-cols-3 border-b border-gray-100">
              <div className="px-5 py-3.5 text-sm text-gray-700">Defective Part Removal</div>
              <div className="px-5 py-3.5 text-center bg-solar-50/40">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div className="px-5 py-3.5 text-center">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>

            {/* Row: New Part Installation */}
            <div className="grid grid-cols-3 border-b border-gray-100">
              <div className="px-5 py-3.5 text-sm text-gray-700">New Part Installation</div>
              <div className="px-5 py-3.5 text-center bg-solar-50/40">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div className="px-5 py-3.5 text-center">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>

            {/* Row: Shipping Included */}
            <div className="grid grid-cols-3 border-b border-gray-100">
              <div className="px-5 py-3.5 text-sm text-gray-700">Shipping Included</div>
              <div className="px-5 py-3.5 text-center bg-solar-50/40">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div className="px-5 py-3.5 text-center">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>

            {/* Row: 25-Year Production Guarantee */}
            <div className="grid grid-cols-3 border-b border-gray-100">
              <div className="px-5 py-3.5 text-sm text-gray-700">25-Year Production Guarantee</div>
              <div className="px-5 py-3.5 text-center bg-solar-50/40">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div className="px-5 py-3.5 text-center">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>

            {/* Row: Performance Monitoring */}
            <div className="grid grid-cols-3">
              <div className="px-5 py-3.5 text-sm text-gray-700">Performance Monitoring</div>
              <div className="px-5 py-3.5 text-center bg-solar-50/40">
                <svg width={20} height={20} className="mx-auto h-5 w-5 text-green-500" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                </svg>
              </div>
              <div className="px-5 py-3.5 text-center text-sm text-gray-400 font-medium">
                Limited
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 3: Our Services ─────────────────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-3xl font-bold text-amber-600">Our Services</h2>
          <p className="mt-2 text-center text-solar-700">
            More than just solar panels — we&apos;re your complete energy partner
          </p>

          <div className="mt-10 grid gap-6 sm:grid-cols-2">
            {/* Solar Panel Installation */}
            <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-solar-100 text-solar-600">
                <svg width={24} height={24} className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-amber-600">Solar Panel Installation</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  Premium Sunburst Solar PV systems custom-designed for your Maryland home. Satellite imagery analysis, transparent pricing, 20/25-point inspections.
                </p>
              </div>
            </div>

            {/* Enphase Battery Backup */}
            <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-sunburst-100 text-sunburst-600">
                <svg width={24} height={24} className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-amber-600">Enphase Battery Backup</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  Store excess energy for nighttime, cloudy days, and outages. Run high-demand appliances when the grid goes down. Monitor from your phone.
                </p>
              </div>
            </div>

            {/* Solar Panel Cleaning */}
            <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-purple-100 text-purple-600">
                <svg width={24} height={24} className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-amber-600">Solar Panel Cleaning</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  Dirty panels lose 15&ndash;25% output. Professional cleaning keeps your system at peak efficiency year-round.
                </p>
              </div>
            </div>

            {/* Electricity Bill Audit */}
            <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm border border-gray-200">
              <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-green-100 text-green-600">
                <svg width={24} height={24} className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base font-semibold text-amber-600">Electricity Bill Audit</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  We review your last 36 months of bills to find overcharges. Many Maryland homeowners have overpaid — we help recover your money.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 4: 6-Step Installation Process ──────────── */}
      <section className="bg-white border-t border-gray-100 py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-3xl font-bold text-amber-600">
            Consider a Solar Power System for Your Home
          </h2>
          <p className="mt-2 text-center text-lg text-solar-600 font-medium">
            Going solar is easier than you think!
          </p>

          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {/* Step 1 */}
            <div className="flex gap-4 rounded-xl bg-white p-5 shadow-sm border border-gray-200">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-solar-600 text-sm font-bold text-white">
                1
              </div>
              <div>
                <h3 className="font-semibold text-amber-600">Custom Proposal</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  We analyze satellite imagery of your roof and electricity usage to design your optimized system with transparent pricing.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4 rounded-xl bg-white p-5 shadow-sm border border-gray-200">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-solar-600 text-sm font-bold text-white">
                2
              </div>
              <div>
                <h3 className="font-semibold text-amber-600">Electronic Agreement</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  Review and sign your agreement digitally. Your price is guaranteed in writing for 60 days.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4 rounded-xl bg-white p-5 shadow-sm border border-gray-200">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-solar-600 text-sm font-bold text-white">
                3
              </div>
              <div>
                <h3 className="font-semibold text-amber-600">Permit Handling</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  We take care of all permitting and paperwork with your local jurisdiction — you don&apos;t have to lift a finger.
                </p>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-4 rounded-xl bg-white p-5 shadow-sm border border-gray-200">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-solar-600 text-sm font-bold text-white">
                4
              </div>
              <div>
                <h3 className="font-semibold text-amber-600">Schedule Installation</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  We coordinate with you to schedule your installation at a time that works. Most installs are completed in 1&ndash;2 days.
                </p>
              </div>
            </div>

            {/* Step 5 */}
            <div className="flex gap-4 rounded-xl bg-white p-5 shadow-sm border border-gray-200">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-solar-600 text-sm font-bold text-white">
                5
              </div>
              <div>
                <h3 className="font-semibold text-amber-600">System Approval</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  After our 25-point post-installation inspection, we coordinate utility approval and interconnection.
                </p>
              </div>
            </div>

            {/* Step 6 */}
            <div className="flex gap-4 rounded-xl bg-white p-5 shadow-sm border border-gray-200">
              <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-solar-600 text-sm font-bold text-white">
                6
              </div>
              <div>
                <h3 className="font-semibold text-amber-600">Activation</h3>
                <p className="mt-1 text-sm text-solar-700 leading-relaxed">
                  Your system goes live! Start generating clean energy and saving money from day one.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 5: Licensed & Insured ───────────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <div className="rounded-xl bg-white p-8 text-center shadow-sm border border-gray-200 sm:p-10">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-solar-100 text-solar-600">
              <svg width={32} height={32} className="h-8 w-8" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <h2 className="mt-5 text-2xl font-bold text-amber-600 sm:text-3xl">
              Licensed &amp; Insured
            </h2>
            <p className="mt-3 text-lg font-semibold text-solar-600">
              Maryland MHIC #165263
            </p>
            <p className="mt-2 text-solar-700">
              Factory-trained, licensed, bonded &amp; insured
            </p>
            <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-gray-50 border border-gray-200 px-5 py-2.5">
              <svg width={20} height={20} className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3H21m-3.75 3H21" />
              </svg>
              <span className="text-sm text-solar-700">
                Backed by Blackstone and Truist, a multi-billion dollar financial institution
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA Break ───────────────────────────────────────── */}
      <CtaBreak />
    </div>
  );
}
