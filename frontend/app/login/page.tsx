"use client";

import React, { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Shield, Lock, User, ArrowRight, AlertCircle, Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectUrl = searchParams.get("redirect") || "/";

  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Please enter both username and password.");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const res = await login(username.trim(), password.trim());
      if (res.success) {
        router.push(redirectUrl);
      } else {
        setError(res.error || "Authentication failed");
      }
    } catch (err: any) {
      setError(err?.message || "An unexpected error occurred during login");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
    setError(null);
  };

  return (
    <div className="max-w-md w-full crystal-card shadow-crystal-dark overflow-hidden animate-in fade-in zoom-in-95 duration-200 border-ivory-300">
      {/* Top Header Banner */}
      <div className="bg-gradient-to-br from-graphite-950 via-graphite-900 to-teal-950 p-6 text-white text-center relative overflow-hidden">
        <div className="absolute right-0 top-0 -mt-6 -mr-6 h-32 w-32 rounded-full bg-teal-500/20 blur-2xl pointer-events-none"></div>

        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-teal-500/20 border border-teal-500/30 text-teal-300 mb-3 shadow-inner">
          <Shield className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold tracking-tight">AlertLens SOC Portal</h1>
        <p className="text-ivory-300 text-xs mt-1">
          Role-Based Access Control & Incident Acknowledgment
        </p>
      </div>

      {/* Form Body */}
      <div className="p-6 md:p-8 space-y-6">
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50/70 p-3.5 text-xs text-rose-800 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-graphite-700 block">
              Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 absolute left-3 top-3 text-graphite-400" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="analyst_demo or admin_demo"
                required
                className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-ivory-300 bg-ivory-50/60 text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/30 focus:border-teal-600"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-graphite-700 block">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 absolute left-3 top-3 text-graphite-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-ivory-300 bg-ivory-50/60 text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/30 focus:border-teal-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="tactile-button w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-xl shadow-crystal-teal transition-all disabled:opacity-50"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <>
                <span>Sign In to Command Center</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Demo Quick-Fill Section */}
        <div className="pt-4 border-t border-ivory-200 space-y-2.5">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-graphite-400 font-mono">
            <Sparkles className="w-3.5 h-3.5 text-teal-600" />
            <span>1-Click Demo Credentials</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("analyst_demo", "demo1234")}
              className="tactile-button text-left p-2.5 rounded-xl border border-ivory-300 hover:border-teal-400 hover:bg-teal-50/40 transition-all text-xs group bg-white shadow-2xs"
            >
              <div className="font-semibold text-graphite-800 group-hover:text-teal-800 flex items-center justify-between">
                <span>Analyst</span>
                <span className="text-[10px] bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded font-bold font-mono">Triage</span>
              </div>
              <div className="text-[10px] text-graphite-500 font-mono mt-0.5">analyst_demo</div>
            </button>

            <button
              type="button"
              onClick={() => handleQuickLogin("admin_demo", "admin1234")}
              className="tactile-button text-left p-2.5 rounded-xl border border-ivory-300 hover:border-indigo-400 hover:bg-indigo-50/40 transition-all text-xs group bg-white shadow-2xs"
            >
              <div className="font-semibold text-graphite-800 group-hover:text-indigo-800 flex items-center justify-between">
                <span>Admin</span>
                <span className="text-[10px] bg-indigo-100 text-indigo-800 px-1.5 py-0.5 rounded font-bold font-mono">Audit</span>
              </div>
              <div className="text-[10px] text-graphite-500 font-mono mt-0.5">admin_demo</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4">
      <Suspense fallback={<div className="w-8 h-8 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>}>
        <LoginForm />
      </Suspense>
    </div>
  );
}
