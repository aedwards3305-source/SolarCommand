"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/solar/why-solar-command", label: "Why Solar Command" },
  { href: "/solar/savings", label: "Savings" },
  { href: "/solar/why-solar", label: "Why Solar" },
  { href: "/solar/batteries", label: "Batteries" },
  { href: "/solar/financing", label: "Financing" },
];

export default function PortalNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(href + "/");

  return (
    <>
      {/* Desktop nav — sits inline in the header flex row */}
      <nav className="hidden md:flex items-center gap-1 ml-6 flex-1">
        {NAV_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`whitespace-nowrap rounded-md px-3 py-1.5 text-base font-medium transition-colors ${
              isActive(link.href)
                ? "bg-white/20 text-white"
                : "text-white/80 hover:text-white hover:bg-white/10"
            }`}
          >
            {link.label}
          </Link>
        ))}
        <Link
          href="/solar/get-quote"
          className={`ml-auto whitespace-nowrap rounded-full px-6 py-2 text-base font-bold transition-colors ${
            isActive("/solar/get-quote")
              ? "bg-white text-solar-700"
              : "bg-white text-solar-700 hover:bg-solar-50"
          }`}
        >
          Get a Quote
        </Link>
      </nav>

      {/* Mobile hamburger */}
      <button
        onClick={() => setOpen(!open)}
        className="md:hidden ml-auto p-2 text-white/80 hover:text-white rounded-md hover:bg-white/10 transition-colors"
        aria-label="Toggle menu"
      >
        <svg
          width={24}
          height={24}
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          {open ? (
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          )}
        </svg>
      </button>

      {/* Mobile dropdown */}
      {open && (
        <div className="md:hidden absolute top-full left-0 right-0 border-t border-solar-800/30 bg-solar-700 shadow-lg z-40">
          <div className="flex flex-col px-4 py-3 gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-3 text-base font-medium transition-colors ${
                  isActive(link.href)
                    ? "bg-white/20 text-white"
                    : "text-white/80 hover:bg-white/10 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="/solar/get-quote"
              onClick={() => setOpen(false)}
              className="mt-1 rounded-lg bg-white px-3 py-3 text-center text-base font-bold text-solar-700 hover:bg-solar-50 transition-colors"
            >
              Get a Quote
            </Link>
          </div>
        </div>
      )}
    </>
  );
}
