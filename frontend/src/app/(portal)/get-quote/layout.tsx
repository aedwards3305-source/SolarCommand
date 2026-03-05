import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Get a Free Solar Quote | Solar Command",
  description: "Request your free solar quote from Solar Command. No obligation, no pressure. Serving Maryland homeowners. MHIC #165263.",
};

export default function GetQuoteLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
