import type { Metadata } from "next";
import Link from "next/link";
import PortalNav from "@/components/portal/PortalNav";

export const metadata: Metadata = {
  title: "Solar Command — Free Solar Quote",
  description:
    "Get your free solar quote from Solar Command. Authorized Sunburst Solar dealer, sponsored by Sunrun. MHIC #165263.",
};

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Header — single clean row */}
      <header className="relative border-b border-gray-200/60 bg-white/90 backdrop-blur-sm sticky top-0 z-30">
        <div className="mx-auto max-w-6xl flex items-center px-4 py-2.5 sm:px-6">
          <Link href="/solar" className="flex items-center gap-2.5 flex-shrink-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/solar-command-logo.jpg"
              alt="Solar Command"
              width={36}
              height={36}
              className="h-9 w-9 rounded-md object-contain"
            />
            <span className="text-base font-bold text-gray-900 sm:text-lg">Solar Command</span>
          </Link>
          <PortalNav />
        </div>
      </header>

      {/* Main */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-solar-900 text-gray-300">
        <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
          <div className="grid gap-8 sm:grid-cols-3">
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">
                Solar Command
              </h4>
              <p className="text-xs leading-relaxed">
                Authorized Sunburst Solar Dealer. Premium solar panels, Enphase
                battery backup, panel cleaning, and electricity bill audits — all
                backed by a comprehensive 25-year warranty with production guarantee.
              </p>
              <p className="mt-2 text-xs text-gray-400">Sponsored by Sunrun</p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">
                Licensed &amp; Certified
              </h4>
              <p className="text-xs leading-relaxed">
                Maryland Home Improvement Commission
                <br />
                MHIC License #165263
              </p>
              <p className="mt-2 text-xs">
                Proudly Serving Maryland
              </p>
              <p className="mt-1 text-xs">
                Factory-trained, licensed, bonded &amp; insured installers
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">
                Get Started
              </h4>
              <p className="text-xs leading-relaxed">
                <Link href="/solar/get-quote" className="hover:text-white transition-colors">
                  Request a Free Quote
                </Link>
              </p>
              <p className="mt-1 text-xs">
                8115 Maplelawn Blvd, Fulton, MD
              </p>
              <p className="mt-3 flex items-center gap-2">
                <span className="inline-block h-2 w-2 rounded-full bg-green-400" />
                <span className="text-xs">Available Mon–Sat, 8am–6pm</span>
              </p>
            </div>
          </div>
          <div className="mt-8 border-t border-solar-800 pt-6 text-center text-xs text-gray-400">
            &copy; {new Date().getFullYear()} Solar Command. All rights
            reserved. Powered by Sunburst Solar.
          </div>
        </div>
      </footer>
    </div>
  );
}
