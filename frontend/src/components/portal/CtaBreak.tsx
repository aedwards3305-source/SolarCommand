import Link from "next/link";

interface CtaBreakProps {
  heading?: string;
  subtext?: string;
}

export default function CtaBreak({
  heading = "Ready to Flip the Switch?",
  subtext = "Start saving today with $0 down financing and the 30% federal tax credit.",
}: CtaBreakProps) {
  return (
    <section className="bg-white py-14 border-t border-gray-100">
      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
        <h2 className="text-3xl font-bold text-amber-600 sm:text-4xl">
          {heading}
        </h2>
        <p className="mt-3 text-lg text-solar-700">{subtext}</p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link
            href="/solar/get-quote"
            className="rounded-full bg-solar-600 px-8 py-3 text-base font-bold text-white shadow-lg hover:bg-solar-700 transition-colors"
          >
            Request Your Free Quote
          </Link>
          <Link
            href="/solar/why-solar-command"
            className="rounded-full border-2 border-solar-600 px-8 py-3 text-base font-bold text-solar-600 hover:bg-solar-50 transition-colors"
          >
            Learn More
          </Link>
        </div>
      </div>
    </section>
  );
}
