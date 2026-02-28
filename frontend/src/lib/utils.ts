export function cn(...classes: (string | boolean | undefined | null)[]) {
  return classes.filter(Boolean).join(" ");
}

export function statusColor(status: string): string {
  const colors: Record<string, string> = {
    hot: "bg-red-100 text-red-800",
    warm: "bg-orange-100 text-orange-800",
    cool: "bg-blue-100 text-blue-800",
    ingested: "bg-gray-100 text-gray-800",
    scored: "bg-purple-100 text-purple-800",
    contacting: "bg-yellow-100 text-yellow-800",
    contacted: "bg-yellow-100 text-yellow-800",
    qualified: "bg-green-100 text-green-800",
    appointment_set: "bg-green-100 text-green-800",
    closed_won: "bg-emerald-100 text-emerald-800",
    closed_lost: "bg-gray-100 text-gray-600",
    dnc: "bg-red-100 text-red-600",
    archived: "bg-gray-100 text-gray-500",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
}

export function formatDate(iso: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function formatCurrency(val: number | null | undefined): string {
  if (val == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(val);
}

export function formatCostUsd(val: number | null | undefined): string {
  if (val == null) return "—";
  if (val < 0.01) return "$" + val.toFixed(4);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(val);
}
