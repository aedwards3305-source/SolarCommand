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
            className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              isActive(link.href)
                ? "bg-solar-100 text-solar-700"
                : "text-gray-600 hover:text-solar-600 hover:bg-gray-50"
            }`}
          >
            {link.label}
          </Link>
        ))}
        <Link
          href="/solar/get-quote"
          className={`ml-auto whitespace-nowrap rounded-full px-5 py-1.5 text-sm font-bold transition-colors ${
            isActive("/solar/get-quote")
              ? "bg-solar-700 text-white"
              : "bg-solar-600 text-white hover:bg-solar-700"
          }`}
        >
          Get a Quote
        </Link>
      </nav>

      {/* Mobile hamburger */}
      <button
        onClick={() => setOpen(!open)}
        className="md:hidden ml-auto p-2 text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors"
        aria-label="Toggle menu"
      >
        <svg
          width={22}
          height={22}
          className="h-[22px] w-[22px]"
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
        <div className="md:hidden absolute top-full left-0 right-0 border-t border-gray-100 bg-white shadow-lg z-40">
          <div className="flex flex-col px-4 py-3 gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive(link.href)
                    ? "bg-solar-100 text-solar-700"
                    : "text-gray-700 hover:bg-gray-50"
                }`}
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="/solar/get-quote"
              onClick={() => setOpen(false)}
              className="mt-1 rounded-lg bg-solar-600 px-3 py-2.5 text-center text-sm font-bold text-white hover:bg-solar-700 transition-colors"
            >
              Get a Quote
            </Link>
          </div>
        </div>
      )}
    </>
  );
}
