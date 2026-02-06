"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900 px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-solar-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <h1 className="mt-4 text-3xl font-bold text-white">SolarCommand</h1>
          <p className="mt-2 text-gray-400">
            Solar Lead Automation System
          </p>
        </div>

        {/* Login form */}
        <form onSubmit={handleSubmit} className="bg-gray-800 rounded-xl p-8 space-y-6 shadow-xl">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full rounded-lg bg-gray-700 border border-gray-600 text-white px-4 py-2.5 focus:ring-2 focus:ring-solar-500 focus:border-transparent outline-none"
              placeholder="admin@solarcommand.local"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-lg bg-gray-700 border border-gray-600 text-white px-4 py-2.5 focus:ring-2 focus:ring-solar-500 focus:border-transparent outline-none"
              placeholder="Enter password"
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-900/50 border border-red-700 p-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-solar-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-solar-700 focus:ring-2 focus:ring-solar-500 focus:ring-offset-2 focus:ring-offset-gray-800 disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-center text-xs text-gray-500">
            First login sets your password automatically
          </p>
        </form>
      </div>
    </div>
  );
}
