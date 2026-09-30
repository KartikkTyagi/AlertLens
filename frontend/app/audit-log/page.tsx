"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ClipboardList,
  ShieldAlert,
  ArrowLeft,
  Clock,
  ExternalLink,
  Shield,
  Eye,
  CheckCircle,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { getAuditLog } from "@/lib/api";
import { AuditLogEntry } from "@/types";

export default function AuditLogPage() {
  const router = useRouter();
  const { user, isAuthenticated, isAdmin, loading: authLoading } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAuditLog();
      setLogs(data);
    } catch (err: any) {
      if (err.message === "FORBIDDEN" || err.message?.includes("403")) {
        setError("Admin role required to view the enterprise audit trail.");
      } else if (err.message === "UNAUTHORIZED" || err.message?.includes("401")) {
        setError("Please log in to access the audit log.");
      } else {
        setError(err?.message || "Failed to load audit trail");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        router.push("/login?redirect=/audit-log");
        return;
      }
      if (!isAdmin) {
        setError("Admin role required to view the enterprise audit trail.");
        setLoading(false);
        return;
      }
      fetchLogs();
    }
  }, [authLoading, isAuthenticated, isAdmin]);

  if (authLoading || (loading && !error)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-10 h-10 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-slate-500 font-medium text-sm animate-pulse">
          Loading enterprise audit trail...
        </p>
      </div>
    );
  }

  if (error || !isAdmin) {
    return (
      <div className="max-w-xl mx-auto my-12 bg-white rounded-2xl border border-rose-200 p-8 shadow-sm text-center">
        <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Access Denied</h2>
        <p className="text-slate-600 mb-6 text-sm">
          {error || "Only administrators (admin_demo) are authorized to inspect the system audit trail."}
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-semibold transition-colors shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link href="/" className="text-slate-400 hover:text-teal-600 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
              <ClipboardList className="w-7 h-7 text-indigo-600" />
              Security Audit Trail
            </h1>
          </div>
          <p className="text-sm text-slate-500 ml-7">
            Immutable log of SOC analyst interactions, AI brief inspects, and human acknowledgments.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 border border-slate-200 bg-white hover:bg-slate-50 rounded-xl text-xs font-semibold text-slate-700 shadow-xs transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh Audit Trail
        </button>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 text-xs text-slate-500">
          <span>
            Total Entries: <strong className="text-slate-800 font-semibold">{logs.length}</strong>
          </span>
          <div className="flex items-center gap-1.5 font-medium text-indigo-600">
            <Shield className="w-3.5 h-3.5" />
            Admin Scoped View
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200/80 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Target Incident</th>
                <th className="py-3 px-4">Log ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-14 text-slate-400">
                    No audit records logged yet.
                  </td>
                </tr>
              ) : (
                logs.map((entry) => (
                  <tr key={entry.log_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap text-[11px]">
                      {new Date(entry.timestamp).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {entry.action === "acknowledged_incident" ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold uppercase tracking-wider">
                          <CheckCircle className="w-3 h-3 text-emerald-500" />
                          Acknowledged Incident
                        </span>
                      ) : entry.action === "viewed_brief" ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-bold uppercase tracking-wider">
                          <Eye className="w-3 h-3 text-blue-500" />
                          Viewed AI Brief
                        </span>
                      ) : (
                        <span className="inline-block px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-semibold">
                          {entry.action}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-semibold text-slate-800 whitespace-nowrap">
                      {entry.user_id || "System"}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {entry.incident_id ? (
                        <Link
                          href={`/incidents/${entry.incident_id}`}
                          className="inline-flex items-center gap-1 font-mono text-[11px] text-teal-600 hover:text-teal-700 bg-teal-50 px-2 py-0.5 rounded hover:underline"
                        >
                          {entry.incident_id.slice(0, 8)}...
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      ) : (
                        <span className="text-slate-400 font-mono">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400 text-[11px] select-all">
                      {entry.log_id.slice(0, 12)}...
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
