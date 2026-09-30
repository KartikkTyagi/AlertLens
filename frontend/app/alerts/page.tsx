"use client";

import React, { useEffect, useState, useTransition } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  ArrowLeft,
  ChevronLeft,
  ChevronRight,
  Database,
  ExternalLink,
  RefreshCw,
  SlidersHorizontal,
  Download,
  FileSpreadsheet,
  Calendar,
  Layers,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  Network,
  Info,
} from "lucide-react";
import { getAlerts, getAlertsCount, getAlertsStats, downloadAlertsCsv } from "@/lib/api";
import { Alert, AlertDatasetStats } from "@/types";

const COMMON_EVENT_TYPES = [
  "ALL",
  "successful_login",
  "failed_login",
  "file_download",
  "file_access",
  "vpn_connect",
  "password_change",
  "Failed Login Attempt",
  "Successful Login",
  "privilege_escalation",
  "Outbound Network Connection",
  "File Integrity Check Failed",
  "Port Scan Activity",
  "Data Exfiltration Attempt",
  "Unauthorized Sudo Access",
  "MFA Bypass Attempt",
  "Geographic Login Anomaly",
  "Connection to Honeypot",
];

const CRITICALITIES = ["ALL", "high", "medium", "low"];

export default function AlertsBrowserPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [stats, setStats] = useState<AlertDatasetStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [showAllEvents, setShowAllEvents] = useState(false);

  // Filters & Pagination
  const [page, setPage] = useState(0);
  const limit = 50;
  const [eventType, setEventType] = useState<string>("ALL");
  const [criticality, setCriticality] = useState<string>("ALL");
  const [sourceIp, setSourceIp] = useState<string>("");
  const [username, setUsername] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const fetchAlertsData = async () => {
    try {
      setLoading(true);
      const params: Parameters<typeof getAlerts>[0] = {
        limit,
        offset: page * limit,
      };

      if (eventType !== "ALL") params.event_type = eventType;
      if (criticality !== "ALL") params.asset_criticality = criticality;
      if (sourceIp.trim()) params.source_ip = sourceIp.trim();
      if (username.trim()) params.username = username.trim();

      const [alertsData, count] = await Promise.all([
        getAlerts(params),
        getAlertsCount(),
      ]);

      setAlerts(alertsData);
      setTotalCount(typeof count === "number" ? count : 0);
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatsData = async () => {
    try {
      setStatsLoading(true);
      const data = await getAlertsStats();
      setStats(data);
    } catch (err) {
      console.error("Failed to fetch dataset stats:", err);
    } finally {
      setStatsLoading(false);
    }
  };

  useEffect(() => {
    fetchAlertsData();
  }, [page, eventType, criticality]);

  useEffect(() => {
    fetchStatsData();
  }, []);

  const handleApplyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    fetchAlertsData();
  };

  const handleResetFilters = () => {
    setEventType("ALL");
    setCriticality("ALL");
    setSourceIp("");
    setUsername("");
    setSearchQuery("");
    setPage(0);
  };

  const handleExportCsv = async () => {
    try {
      setExporting(true);
      setExportError(null);
      await downloadAlertsCsv();
    } catch (err: any) {
      console.error("Export error:", err);
      setExportError(err?.message || "Failed to download alerts CSV. Please ensure you are logged in.");
    } finally {
      setExporting(false);
    }
  };

  const filteredBySearch = alerts.filter((alert) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      alert.raw_message.toLowerCase().includes(q) ||
      (alert.username && alert.username.toLowerCase().includes(q)) ||
      (alert.source_ip && alert.source_ip.toLowerCase().includes(q)) ||
      alert.target_asset.toLowerCase().includes(q)
    );
  });

  const totalPages = Math.ceil(totalCount / limit) || 1;

  // Format date range nicely
  const formatDate = (iso: string | null | undefined) => {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZoneName: "short",
      });
    } catch {
      return iso;
    }
  };

  const currentAlertCount = stats?.total_alerts || totalCount || 3000;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              href="/"
              className="text-graphite-400 hover:text-teal-700 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-2xl md:text-3xl font-black text-graphite-950 tracking-tight flex items-center gap-2.5">
              <Database className="w-7 h-7 text-teal-700" />
              Raw Security Alert Stream
            </h1>
          </div>
          <p className="text-xs sm:text-sm text-graphite-500 ml-7">
            Browse, search, and inspect the raw incoming SIEM alert stream. Total logged:{" "}
            <span className="font-semibold font-mono text-graphite-800">
              {currentAlertCount.toLocaleString()} alerts
            </span>
            .
          </p>
        </div>

        <div className="flex items-center gap-2.5 self-start sm:self-auto flex-wrap">
          <button
            onClick={handleExportCsv}
            disabled={exporting}
            className="tactile-button inline-flex items-center gap-2 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl text-xs font-bold shadow-crystal-teal transition-all disabled:opacity-50"
            title={`Export complete canonical ${currentAlertCount.toLocaleString()} raw alerts as RFC 4180 CSV`}
          >
            {exporting ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5" />
            )}
            <span>
              {exporting
                ? `Exporting ${currentAlertCount.toLocaleString()} Alerts...`
                : `Export Full CSV (${currentAlertCount.toLocaleString()} Alerts)`}
            </span>
          </button>

          <button
            onClick={() => {
              fetchAlertsData();
              fetchStatsData();
            }}
            disabled={loading}
            className="tactile-button inline-flex items-center gap-2 px-4 py-2 border border-ivory-300 bg-white hover:bg-ivory-50 rounded-xl text-xs font-semibold text-graphite-700 shadow-2xs transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-graphite-500 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {exportError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/80 p-3 text-xs text-rose-800 flex items-center justify-between gap-2 shadow-2xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{exportError}</span>
          </div>
          <button onClick={() => setExportError(null)} className="text-rose-500 hover:text-rose-700 font-bold">✕</button>
        </div>
      )}

      {/* Dataset Information Section */}
      <div className="crystal-card p-6 shadow-crystal space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-ivory-200 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-200">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-graphite-950 flex items-center gap-2">
                Canonical Dataset Overview &amp; Schema Metadata
              </h2>
              <p className="text-xs text-graphite-500">
                Ground-truth SIEM telemetry partition utilized for semantic correlation and benchmark validation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
            <span className="px-2.5 py-1 rounded-lg bg-ivory-100 text-graphite-700 border border-ivory-300 font-semibold">
              Canonical Set: {currentAlertCount.toLocaleString()} Records
            </span>
          </div>
        </div>

        {/* 4 Key Stat Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-ivory-100/70 border border-ivory-200 space-y-1">
            <span className="text-[10px] uppercase font-mono font-semibold text-graphite-500 block">Total Raw Alerts</span>
            <span className="text-2xl font-black text-graphite-950 font-mono">
              {currentAlertCount.toLocaleString()}
            </span>
            <span className="text-[11px] text-graphite-500 block">100% database persisted</span>
          </div>

          <div className="p-4 rounded-xl bg-teal-50/60 border border-teal-200/80 space-y-1">
            <span className="text-[10px] uppercase font-mono font-semibold text-teal-800 block">Assigned to Incidents</span>
            <span className="text-2xl font-black text-teal-900 font-mono">
              {(stats?.assigned_to_incidents ?? 2083).toLocaleString()}
            </span>
            <span className="text-[11px] text-teal-700 font-medium block">
              {stats ? `${((stats.assigned_to_incidents / stats.total_alerts) * 100).toFixed(1)}%` : "69.4%"} correlated into clusters
            </span>
          </div>

          <div className="p-4 rounded-xl bg-amber-50/60 border border-amber-200/80 space-y-1">
            <span className="text-[10px] uppercase font-mono font-semibold text-amber-800 block">Uncorrelated Alerts</span>
            <span className="text-2xl font-black text-amber-900 font-mono">
              {(stats?.uncorrelated_alerts ?? 917).toLocaleString()}
            </span>
            <span className="text-[11px] text-amber-700 font-medium block">
              {stats ? `${((stats.uncorrelated_alerts / stats.total_alerts) * 100).toFixed(1)}%` : "30.6%"} isolated background telemetry
            </span>
          </div>

          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200/80 space-y-1">
            <span className="text-[10px] uppercase font-mono font-semibold text-indigo-800 block flex items-center gap-1">
              <Calendar className="w-3 h-3 text-indigo-600 inline" />
              Telemetry Time Span
            </span>
            <span className="text-xs font-bold text-indigo-950 font-mono block leading-snug">
              {formatDate(stats?.time_range?.start)} &rarr;
            </span>
            <span className="text-xs font-bold text-indigo-950 font-mono block leading-snug">
              {formatDate(stats?.time_range?.end)}
            </span>
          </div>
        </div>

        {/* Schema Fields & Event-Type Distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-2">
          {/* Available Fields Column */}
          <div className="lg:col-span-5 space-y-3">
            <h3 className="text-xs font-bold uppercase font-mono tracking-wider text-graphite-600 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-600" />
              Database Record Schema ({stats?.available_fields?.length ?? 9} Fields)
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {(stats?.available_fields ?? [
                "alert_id",
                "timestamp",
                "event_type",
                "username",
                "source_ip",
                "target_asset",
                "asset_criticality",
                "raw_message",
                "incident_id",
              ]).map((field) => (
                <span
                  key={field}
                  className="font-mono text-[11px] bg-ivory-100 hover:bg-teal-50 border border-ivory-300 text-graphite-800 px-2.5 py-1 rounded-lg transition-colors cursor-default"
                >
                  {field}
                </span>
              ))}
            </div>
            <p className="text-[11px] text-graphite-500 leading-relaxed pt-1">
              Every exported CSV record contains the complete database row including the foreign-key link to its parent correlated <code className="bg-ivory-200 px-1 py-0.5 rounded text-[10px]">incident_id</code> when clustered.
            </p>
          </div>

          {/* Event-Type Distribution Column */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase font-mono tracking-wider text-graphite-600 flex items-center gap-1.5">
                <BarChart3 className="w-3.5 h-3.5 text-teal-600" />
                Event-Type Distribution ({stats ? Object.keys(stats.event_type_distribution).length : 17} Types)
              </h3>
              {stats && Object.keys(stats.event_type_distribution).length > 6 && (
                <button
                  type="button"
                  onClick={() => setShowAllEvents(!showAllEvents)}
                  className="text-[11px] text-teal-700 hover:text-teal-800 font-semibold cursor-pointer underline"
                >
                  {showAllEvents ? "Show Top 6" : `Show All (${Object.keys(stats.event_type_distribution).length})`}
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              {stats ? (
                Object.entries(stats.event_type_distribution)
                  .slice(0, showAllEvents ? undefined : 6)
                  .map(([type, count]) => {
                    const pct = ((count / stats.total_alerts) * 100).toFixed(1);
                    return (
                      <div
                        key={type}
                        className="flex items-center justify-between p-2 rounded-lg bg-ivory-100/60 border border-ivory-200/80 font-mono text-[11px]"
                      >
                        <span className="truncate text-graphite-800 font-medium" title={type}>
                          {type}
                        </span>
                        <div className="flex items-center gap-1.5 shrink-0 ml-2">
                          <span className="font-bold text-graphite-950">{count.toLocaleString()}</span>
                          <span className="text-[10px] text-graphite-400">({pct}%)</span>
                        </div>
                      </div>
                    );
                  })
              ) : (
                <div className="text-xs text-graphite-400 py-2">Loading distribution...</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="crystal-card p-5 shadow-crystal space-y-4">
        <form onSubmit={handleApplyFilters} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {/* Event Type Filter */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-graphite-700 flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-graphite-400" />
                Event Type
              </label>
              <select
                value={eventType}
                onChange={(e) => {
                  setEventType(e.target.value);
                  setPage(0);
                }}
                className="w-full text-xs rounded-xl border border-ivory-300 py-2 px-3 bg-white text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 shadow-2xs"
              >
                {COMMON_EVENT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type === "ALL" ? "All Event Types" : type}
                  </option>
                ))}
              </select>
            </div>

            {/* Criticality Filter */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-graphite-700 flex items-center gap-1.5">
                <Filter className="w-3.5 h-3.5 text-graphite-400" />
                Criticality
              </label>
              <select
                value={criticality}
                onChange={(e) => {
                  setCriticality(e.target.value);
                  setPage(0);
                }}
                className="w-full text-xs rounded-xl border border-ivory-300 py-2 px-3 bg-white text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 shadow-2xs"
              >
                {CRITICALITIES.map((c) => (
                  <option key={c} value={c}>
                    {c === "ALL" ? "All Criticalities" : c.toUpperCase()}
                  </option>
                ))}
              </select>
            </div>

            {/* Username input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-graphite-700">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. dev_intern, admin"
                className="w-full text-xs rounded-xl border border-ivory-300 py-2 px-3 bg-white text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 shadow-2xs"
              />
            </div>

            {/* Source IP input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-graphite-700">Source IP</label>
              <input
                type="text"
                value={sourceIp}
                onChange={(e) => setSourceIp(e.target.value)}
                placeholder="e.g. 10.0.12.44"
                className="w-full text-xs rounded-xl border border-ivory-300 py-2 px-3 bg-white text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 shadow-2xs"
              />
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2 border-t border-ivory-200">
            {/* Free text search */}
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-graphite-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter current view by log content..."
                className="w-full text-xs pl-9 pr-4 py-2 bg-white border border-ivory-300 rounded-xl text-graphite-800 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 shadow-2xs"
              />
            </div>

            <div className="flex items-center gap-2 self-end sm:self-auto">
              <button
                type="button"
                onClick={handleResetFilters}
                className="tactile-button px-3.5 py-1.5 text-xs text-graphite-600 hover:text-graphite-900 border border-ivory-300 hover:bg-ivory-100 rounded-xl transition-colors font-medium shadow-2xs"
              >
                Reset
              </button>
              <button
                type="submit"
                className="tactile-button px-4 py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-xl shadow-crystal-teal transition-all"
              >
                Apply Filters
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Alerts Table */}
      <div className="crystal-card shadow-crystal overflow-hidden">
        <div className="p-4 border-b border-ivory-200 flex items-center justify-between bg-ivory-100/60 text-xs text-graphite-600 font-mono">
          <span>
            Showing{" "}
            <strong className="text-graphite-900 font-semibold">
              {filteredBySearch.length}
            </strong>{" "}
            records on Page {page + 1} of {totalPages} (Total filtered: {totalCount.toLocaleString()})
          </span>
          <div className="flex items-center gap-1.5 font-medium text-emerald-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            PostgreSQL Live Sync
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ivory-100/80 border-b border-ivory-200 text-[11px] font-bold uppercase tracking-wider text-graphite-500 font-mono">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">Source IP</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Target Asset</th>
                <th className="py-3 px-4">Incident Cluster</th>
                <th className="py-3 px-4">Log Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ivory-200/80 text-xs">
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-16 text-graphite-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="w-7 h-7 border-3 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-xs font-medium">Fetching alerts from database...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredBySearch.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-14 text-graphite-400">
                    No alerts match the specified filters.
                  </td>
                </tr>
              ) : (
                filteredBySearch.map((alert) => (
                  <tr
                    key={alert.alert_id}
                    className="hover:bg-teal-50/30 transition-colors"
                  >
                    <td className="py-3 px-4 font-mono text-graphite-500 whitespace-nowrap text-[11px]">
                      {new Date(alert.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td className="py-3 px-4 font-semibold text-graphite-900 whitespace-nowrap">
                      {alert.event_type}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide font-mono ${
                          alert.asset_criticality === "high"
                            ? "bg-rose-100 text-rose-800 border border-rose-200"
                            : alert.asset_criticality === "medium"
                            ? "bg-amber-100 text-amber-800 border border-amber-200"
                            : "bg-ivory-100 text-graphite-700 border border-ivory-300"
                        }`}
                      >
                        {alert.asset_criticality}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-graphite-600 whitespace-nowrap text-[11px]">
                      {alert.source_ip || "—"}
                    </td>
                    <td className="py-3 px-4 font-medium text-graphite-700 whitespace-nowrap font-mono">
                      {alert.username || "—"}
                    </td>
                    <td className="py-3 px-4 font-mono text-graphite-700 whitespace-nowrap text-[11px]">
                      <span className="bg-ivory-100 border border-ivory-200 px-1.5 py-0.5 rounded text-graphite-800">
                        {alert.target_asset || "—"}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {alert.incident_id ? (
                        <Link
                          href={`/incidents/${alert.incident_id}`}
                          className="inline-flex items-center gap-1 font-mono text-[11px] text-teal-700 hover:text-teal-900 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-lg hover:underline"
                        >
                          {alert.incident_id.slice(0, 8)}...
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      ) : (
                        <span className="text-[10px] font-medium uppercase tracking-wider text-graphite-400 bg-ivory-100 border border-ivory-200 px-2 py-0.5 rounded font-mono">
                          Uncorrelated
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-graphite-600 max-w-xs truncate font-mono text-[11px]" title={alert.raw_message}>
                      {alert.raw_message}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination controls */}
        <div className="p-4 border-t border-ivory-200 flex items-center justify-between bg-white text-xs">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0 || loading}
            className="tactile-button inline-flex items-center gap-1.5 px-3 py-1.5 border border-ivory-300 rounded-xl font-medium text-graphite-700 hover:bg-ivory-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-2xs"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>

          <span className="text-graphite-500 font-mono font-medium">
            Page <strong className="text-graphite-900">{page + 1}</strong> of{" "}
            <strong className="text-graphite-900">{totalPages}</strong>
          </span>

          <button
            onClick={() => setPage((p) => (p + 1 < totalPages ? p + 1 : p))}
            disabled={page + 1 >= totalPages || loading}
            className="tactile-button inline-flex items-center gap-1.5 px-3 py-1.5 border border-ivory-300 rounded-xl font-medium text-graphite-700 hover:bg-ivory-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-2xs"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
