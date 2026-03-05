import type { Metadata } from "next";
import PageHero from "@/components/portal/PageHero";
import CtaBreak from "@/components/portal/CtaBreak";

export const metadata: Metadata = {
  title: "Why Go Solar | Benefits of Solar Energy | Solar Command",
  description:
    "Discover the benefits of solar energy for your Maryland home. Reduce your carbon footprint, achieve energy independence, and save money.",
};

const BENEFITS = [
  {
    title: "Environmentally Friendly",
    description:
      "Solar energy dramatically reduces your carbon footprint. Unlike fossil fuels, solar panels produce clean, renewable energy with zero emissions. Every kilowatt-hour of solar energy helps combat climate change.",
    icon: (
      <svg
        width={32}
        height={32}
        className="h-8 w-8"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12.75 3.03v.568c0 .334.148.65.405.864l1.068.89c.442.369.535 1.01.216 1.49l-.51.766a2.25 2.25 0 01-1.161.886l-.143.048a1.107 1.107 0 00-.57 1.664c.369.555.169 1.307-.427 1.605L9 13.125l.423 1.059a.956.956 0 01-1.652.928l-.679-.906a1.125 1.125 0 00-1.906.172L4.5 15.75l-.612.153M12.75 3.031a9 9 0 00-8.862 12.872M12.75 3.031a9 9 0 016.69 14.036m0 0l-.177-.529A2.25 2.25 0 0017.128 15H16.5l-.324-.324a1.453 1.453 0 00-2.328.377l-.036.073a1.586 1.586 0 01-.982.816l-.99.282c-.55.157-.894.702-.8 1.267l.073.438c.08.474.49.821.97.821.846 0 1.598.542 1.865 1.345l.215.643m5.276-3.67a9.012 9.012 0 01-5.276 3.67"
        />
      </svg>
    ),
    iconBg: "bg-green-100 text-green-600",
  },
  {
    title: "Energy Independence",
    description:
      "Generate your own electricity and protect yourself from grid outages and rising utility costs. With an Enphase battery backup, you can power your home even when the grid goes down.",
    icon: (
      <svg
        width={32}
        height={32}
        className="h-8 w-8"
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
    ),
    iconBg: "bg-solar-100 text-solar-600",
  },
  {
    title: "Cost Savings",
    description:
      "A quality solar system reduces your electric bill by 50 to 90 percent. With Maryland's net metering program, excess energy your panels produce gets credited back to you by your utility company.",
    icon: (
      <svg
        width={32}
        height={32}
        className="h-8 w-8"
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
    ),
    iconBg: "bg-green-100 text-green-600",
  },
  {
    title: "Predictable Payments",
    description:
      "Lock in a fixed energy cost instead of being subject to rising utility rates. Utility prices have increased 16% over the past decade \u2014 solar gives you price certainty for 25+ years.",
    icon: (
      <svg
        width={32}
        height={32}
        className="h-8 w-8"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5m-9-6h.008v.008H12v-.008zM12 15h.008v.008H12V15zm0 2.25h.008v.008H12v-.008zM9.75 15h.008v.008H9.75V15zm0 2.25h.008v.008H9.75v-.008zM7.5 15h.008v.008H7.5V15zm0 2.25h.008v.008H7.5v-.008zm6.75-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V15zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H16.5v-.008zm0 2.25h.008v.008H16.5V15z"
        />
      </svg>
    ),
    iconBg: "bg-sunburst-100 text-sunburst-600",
  },
  {
    title: "Increased Home Value",
    description:
      "Homes with solar panels sell for an average of $15,000 more than comparable homes without. Solar is an investment that pays you back when you sell.",
    icon: (
      <svg
        width={32}
        height={32}
        className="h-8 w-8"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
        />
      </svg>
    ),
    iconBg: "bg-solar-100 text-solar-600",
  },
];

export default function WhySolarPage() {
  return (
    <div>
      <PageHero
        title="Why Solar Energy"
        subtitle="The Benefits of Clean, Renewable Power"
        description="Going solar is one of the smartest investments you can make for your home, your wallet, and the planet."
      />

      {/* ── Section 1: Benefit Blocks ──────────────────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <div className="space-y-6">
            {BENEFITS.map((benefit) => (
              <div
                key={benefit.title}
                className="flex flex-col gap-5 rounded-xl bg-white p-6 shadow-sm border border-gray-200 sm:flex-row sm:items-start"
              >
                <div
                  className={`flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-xl ${benefit.iconBg}`}
                >
                  {benefit.icon}
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-amber-600">
                    {benefit.title}
                  </h3>
                  <p className="mt-2 text-base text-solar-700 leading-relaxed">
                    {benefit.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Section 2: Environmental Impact Stats ─────────────── */}
      <section className="bg-solar-900 py-14">
        <div className="mx-auto max-w-5xl px-4 sm:px-6">
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
            Help Save the Planet with Solar
          </h2>
          <p className="mt-2 text-center text-base text-gray-400">
            Estimated environmental impact of our customers over 20 years
          </p>
          <div className="mt-10 grid gap-6 sm:grid-cols-3">
            {/* Trees Planted Equivalent */}
            <div className="text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gray-800">
                <svg
                  width={28}
                  height={28}
                  className="h-7 w-7 text-green-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
                  />
                </svg>
              </div>
              <p className="mt-4 text-4xl font-extrabold text-green-400 sm:text-5xl">
                498,000
              </p>
              <p className="mt-1 text-base text-gray-400">
                Trees Planted Equivalent
              </p>
            </div>

            {/* Gallons of Gas Saved */}
            <div className="text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gray-800">
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
                    d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z"
                  />
                </svg>
              </div>
              <p className="mt-4 text-4xl font-extrabold text-solar-400 sm:text-5xl">
                395,400
              </p>
              <p className="mt-1 text-base text-gray-400">
                Gallons of Gas Saved
              </p>
            </div>

            {/* Miles of Driving Reduced */}
            <div className="text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gray-800">
                <svg
                  width={28}
                  height={28}
                  className="h-7 w-7 text-sunburst-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12"
                  />
                </svg>
              </div>
              <p className="mt-4 text-4xl font-extrabold text-sunburst-400 sm:text-5xl">
                8,421,560
              </p>
              <p className="mt-1 text-base text-gray-400">
                Miles of Driving Reduced
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 3: CTA Text ───────────────────────────────── */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="text-4xl font-bold text-amber-600">
            Start Your Solar Journey Today
          </h2>
          <p className="mt-4 text-xl text-solar-700 leading-relaxed">
            Maryland homeowners are saving thousands with solar energy. Join them
            today.
          </p>
        </div>
      </section>

      {/* ── CTA Break ─────────────────────────────────────────── */}
      <CtaBreak />
    </div>
  );
}
