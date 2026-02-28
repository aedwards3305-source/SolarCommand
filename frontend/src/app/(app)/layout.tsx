"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import Sidebar from "@/components/layout/Sidebar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, hasToken } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Only redirect to login when there is genuinely no auth
    // (no token in localStorage). If the token exists but api.me()
    // failed transiently, keep showing the app instead of logging out.
    if (!loading && !user && !hasToken) {
      router.replace("/login");
    }
  }, [user, loading, hasToken, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="animate-pulse text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!user && !hasToken) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-64 flex-1 p-6">{children}</main>
    </div>
  );
}
