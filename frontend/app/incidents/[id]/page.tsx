"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ShieldAlert,
  Clock,
  Layers,
  Sparkles,
  Database,
  ChevronRight,
  AlertTriangle,
  Info,
  CheckCircle2,
  CheckCircle,
  Calculator,
  Activity,
  Network,
  Crosshair,
  ShieldCheck,
  Cpu,
  RefreshCw,
} from "lucide-react";
import {
  getIncident,
  getIncidentAlerts,
  getIncidentBrief,
  acknowledgeIncident,
  generateIncidentBrief,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Incident, IncidentBrief, Alert } from "@/types";
import { SeverityBadge } from "@/components/SeverityBadge";
import { MitreBadge } from "@/components/MitreBadge";
import { BriefDisplay } from "@/components/BriefDisplay";
import { GlossaryTooltip } from "@/components/GlossaryTooltip";

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const incidentId = params?.id as string;

  const { isAuthenticated, loading: authLoading } = useAuth();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [brief, setBrief] = useState<IncidentBrief | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [acknowledging, setAcknowledging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/login?redirect=/incidents/${incidentId}`);
    }
  }, [authLoading, isAuthenticated, incidentId, router]);

  useEffect(() => {
    if (!incidentId || !isAuthenticated) return;

    let isMounted = true;
    async function loadIncidentData() {
      try {
        setLoading(true);
        setError(null);

        const [incData, briefData, alertsData] = await Promise.all([
          getIncident(incidentId),
          getIncidentBrief(incidentId),
          getIncidentAlerts(incidentId),
        ]);

        if (isMounted) {
          setIncident(incData);
          setBrief(briefData);
          setAlerts(alertsData);
        }
      } catch (err: any) {
        if (isMounted) {
          if (err.message === "UNAUTHORIZED" || err.message?.includes("401")) {
            router.push(`/login?redirect=/incidents/${incidentId}`);
            return;
          }
          console.error("Error loading incident details:", err);
          setError(err?.message || "Failed to load incident details");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    loadIncidentData();
    return () => {
      isMounted = false;
    };
  }, [incidentId, isAuthenticated, router]);

  const handleAcknowledge = async () => {
    if (!incidentId || incident?.acknowledged) return;

    try {
      setAcknowledging(true);
      const updated = await acknowledgeIncident(incidentId);
      setIncident(updated);
    } catch (err: any) {
      console.error("Failed to acknowledge incident:", err);
      alert("Failed to acknowledge incident: " + (err.message || "Unknown error"));
    } finally {
      setAcknowledging(false);
    }
  };

  const handleGenerateBrief = async () => {
    if (!incidentId) return;
    const newBrief = await generateIncidentBrief(incidentId);
    setBrief(newBrief);
  };

  if (authLoading || (loading && !error)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-10 h-10 border-4 border-teal-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-graphite-500 font-medium text-sm animate-pulse">
          Loading incident {incidentId ? `${incidentId.slice(0, 8)}...` : ""} details...
        </p>
      </div>
    );
  }

  if (error || !incident) {
    return (
      <div className="max-w-4xl mx-auto my-12 crystal-card p-8 text-center border-rose-200">
        <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto mb-4 border border-rose-200">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-graphite-900 mb-2">Incident Not Found</h2>
        <p className="text-graphite-600 mb-6 text-sm">
          {error || `Could not find incident with ID "${incidentId}".`}
        </p>
        <Link
          href="/"
          className="tactile-button inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-sm font-semibold shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Breadcrumb & Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-graphite-500">
          <Link
            href="/"
            className="hover:text-teal-700 transition-colors flex items-center gap-1 font-medium"
          >
            Dashboard
          </Link>
          <ChevronRight className="w-4 h-4 text-graphite-400" />
          <span className="font-mono text-xs bg-ivory-100 text-graphite-700 px-2.5 py-0.5 rounded-md border border-ivory-300">
            {incident.incident_id.slice(0, 12)}...
          </span>
        </div>

        <Link
          href="/"
          className="tactile-button inline-flex items-center gap-2 px-4 py-2 border border-ivory-300 hover:bg-ivory-100 text-graphite-700 rounded-xl text-sm font-medium transition-colors bg-white shadow-2xs"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Dashboard
        </Link>
      </div>

      {/* Incident Header Card with Acknowledgment Action */}
      <div className="crystal-card p-6 md:p-8 shadow-crystal">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 bg-graphite-950 text-white rounded-lg font-mono shadow-xs">
                Rank #{incident.severity_rank}
              </span>
              <div className="inline-flex items-center gap-1">
                <SeverityBadge score={incident.severity_score} />
                <GlossaryTooltip term="severity_score" position="bottom" />
              </div>
              <div className="inline-flex items-center gap-1">
                <MitreBadge
                  tag={incident.mitre_tag}
                  techniqueName={incident.mitre_technique_name}
                  showFullName={true}
                />
                <GlossaryTooltip term="mitre_technique" position="bottom" />
              </div>
              <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-semibold ${
                incident.confidence_tier === "actionable"
                  ? "bg-teal-50 text-teal-900 border-teal-200"
                  : "bg-amber-50 text-amber-900 border-amber-200"
              }`}>
                <span>{incident.confidence_tier === "actionable" ? "Actionable Tier" : "Informational Tier"}</span>
                <GlossaryTooltip term="confidence_tier" position="bottom" />
              </span>

              {/* Acknowledgment Pill */}
              {incident.acknowledged ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                  <span>
                    Acknowledged by {incident.acknowledged_by}
                  </span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-ivory-100 text-graphite-600 border border-ivory-300 text-xs font-medium">
                  <span>Pending Triage</span>
                </span>
              )}
            </div>

            <div className="space-y-1">
              <h1 className="text-2xl md:text-3xl font-black text-graphite-950 tracking-tight">
                Incident Forensics &amp; Intelligence
              </h1>
              <p className="text-xs font-mono text-graphite-400 select-all">
                ID: {incident.incident_id}
              </p>
            </div>
          </div>

          {/* Quick Metrics & Human-in-the-Loop Acknowledge Button */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="flex items-center gap-4 bg-ivory-100/70 border border-ivory-300/80 rounded-2xl p-4 shadow-2xs">
              <div className="text-center px-3 border-r border-ivory-300">
                <span className="block text-[10px] uppercase tracking-wider font-semibold text-graphite-500">
                  Score
                </span>
                <span className="text-2xl font-black text-graphite-950 font-mono">
                  {incident.severity_score.toFixed(2)}
                </span>
              </div>
              <div className="text-center px-3 border-r border-ivory-300">
                <span className="block text-[10px] uppercase tracking-wider font-semibold text-graphite-500">
                  Alerts
                </span>
                <span className="text-2xl font-black text-teal-700 flex items-center justify-center gap-1 font-mono">
                  <Layers className="w-4 h-4 text-teal-600 inline" />
                  {incident.alert_count}
                </span>
              </div>
              <div className="text-left px-2">
                <span className="block text-[10px] uppercase tracking-wider font-semibold text-graphite-500">
                  Created
                </span>
                <span className="text-xs font-medium text-graphite-700 flex items-center gap-1 mt-0.5 font-mono">
                  <Clock className="w-3.5 h-3.5 text-graphite-400" />
                  {new Date(incident.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </div>

            {/* Human-in-the-Loop Action Button */}
            {!incident.acknowledged ? (
              <button
                onClick={handleAcknowledge}
                disabled={acknowledging}
                className="tactile-button flex items-center justify-center gap-2 px-5 py-4 bg-teal-700 hover:bg-teal-800 text-white rounded-2xl text-xs font-bold shadow-crystal-teal transition-all disabled:opacity-50"
              >
                {acknowledging ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                <span>Acknowledge Incident</span>
              </button>
            ) : (
              <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-2xl text-left shadow-2xs">
                <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5 font-mono">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                  Human Acknowledged
                </div>
                <div className="text-xs text-emerald-700 font-medium mt-0.5">
                  By {incident.acknowledged_by}
                </div>
                {incident.acknowledged_at && (
                  <div className="text-[10px] text-emerald-600 font-mono mt-0.5">
                    {new Date(incident.acknowledged_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 5 Independent Intelligence Dimensions Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-graphite-500 font-mono flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal-600"></span>
            Five-Dimension Intelligence Model (Strictly Independent Context)
          </h2>
          <span className="text-xs text-graphite-400">Additive Score Pollution Prevented</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Dimension 1: Primary Severity Score */}
          <div className="crystal-card p-5 shadow-crystal space-y-3 border-teal-200/80">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-200">
                  <Calculator className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-graphite-900">1. Severity Score</h3>
                  <p className="text-[11px] text-graphite-500">Primary Ranking Dimension</p>
                </div>
              </div>
              <span className="text-lg font-black text-teal-700 font-mono">
                {incident.severity_score.toFixed(2)}
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-xl bg-ivory-100/70 border border-ivory-200 font-mono text-[11px]">
                <span className="text-graphite-500 block">3-Factor Composite Formula:</span>
                <span className="text-teal-800 font-semibold">(Asset × 3) + (Event × 2) + ln(N+1)</span>
              </div>
              <p className="text-[11px] text-graphite-500 leading-relaxed">
                Deterministic mathematical scoring ensuring reproducible triage priority without arbitrary weights.
              </p>
            </div>
          </div>

          {/* Dimension 2: Attack Progression */}
          <div className="crystal-card p-5 shadow-crystal space-y-3 border-purple-200/80">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center border border-purple-200">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-graphite-900">2. Attack Progression</h3>
                  <p className="text-[11px] text-graphite-500">Independent Behavioral Context</p>
                </div>
              </div>
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-lg border font-mono ${
                  incident.attack_progression === "Advanced Kill-Chain Detected"
                    ? "bg-purple-100 text-purple-800 border-purple-300"
                    : incident.attack_progression === "Escalation Chain Detected"
                    ? "bg-indigo-100 text-indigo-800 border-indigo-300"
                    : "bg-ivory-100 text-graphite-700 border-ivory-300"
                }`}
              >
                {incident.attack_progression ? incident.attack_progression.split(" ")[0] : "Isolated"}
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-xl bg-ivory-100/70 border border-ivory-200 font-mono text-[11px]">
                <span className="text-graphite-500 block">Observed Sequence:</span>
                <span className="text-purple-900 font-semibold truncate block">
                  {incident.progression_detail || "Single lifecycle stage"}
                </span>
              </div>
              <p className="text-[11px] text-graphite-500 leading-relaxed">
                Multi-stage kill chain progression. Strictly qualitative context; never added to the numerical score.
              </p>
            </div>
          </div>

          {/* Dimension 3: Correlation Confidence */}
          <div className="crystal-card p-5 shadow-crystal space-y-3 border-teal-200/80">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-200">
                  <Network className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-graphite-900">3. Correlation Confidence</h3>
                  <p className="text-[11px] text-graphite-500">Evidence Cohesion Metric</p>
                </div>
              </div>
              <span className="text-lg font-black text-teal-700 font-mono">
                {Math.round((incident.correlation_confidence ?? 0.75) * 100)}%
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-xl bg-ivory-100/70 border border-ivory-200 font-mono text-[11px]">
                <span className="text-graphite-500 block">Cohesion Basis:</span>
                <span className="text-teal-900 font-semibold truncate block">
                  {incident.confidence_reason || "Multi-entity graph linkage"}
                </span>
              </div>
              <p className="text-[11px] text-graphite-500 leading-relaxed">
                Measures graph topology &amp; entity cohesion across alerts. Does NOT assert malicious probability.
              </p>
            </div>
          </div>

          {/* Dimension 4: MITRE ATT&CK */}
          <div className="crystal-card p-5 shadow-crystal space-y-3 border-indigo-200/80">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center border border-indigo-200">
                  <Crosshair className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-graphite-900">4. MITRE ATT&amp;CK</h3>
                  <p className="text-[11px] text-graphite-500">Validated Technique Context</p>
                </div>
              </div>
              <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-100/80 px-2 py-0.5 rounded border border-indigo-200">
                {incident.mitre_tag || "Untagged"}
              </span>
            </div>
            <div className="space-y-2 text-xs">
              <div className="p-3 rounded-xl bg-ivory-100/70 border border-ivory-200 font-mono text-[11px]">
                <span className="text-graphite-500 block">Technique Name:</span>
                <span className="text-indigo-900 font-semibold truncate block">
                  {incident.mitre_technique_name || "General Telemetry"}
                </span>
              </div>
              <p className="text-[11px] text-graphite-500 leading-relaxed">
                Defines adversarial tactics, techniques, and procedures (TTPs) mapped to standard MITRE framework.
              </p>
            </div>
          </div>

          {/* Dimension 5: Actionability Triage */}
          <div className="crystal-card p-5 shadow-crystal space-y-3 border-amber-200/80 md:col-span-2 lg:col-span-2">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-200">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-graphite-900">5. Actionability Triage</h3>
                  <p className="text-[11px] text-graphite-500">Deterministic P90 or MITRE Alignment</p>
                </div>
              </div>
              <span className={`text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-lg border font-mono ${
                incident.confidence_tier === "actionable"
                  ? "bg-teal-100 text-teal-800 border-teal-300"
                  : "bg-amber-100 text-amber-800 border-amber-300"
              }`}>
                {incident.confidence_tier === "actionable" ? "Actionable Threat" : "Informational Cluster"}
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-ivory-100/70 border border-ivory-200 font-mono text-[11px]">
                <span className="text-graphite-500 block">Actionability Rule:</span>
                <span className="text-graphite-900 font-semibold">
                  MITRE Tagged OR Severity &ge; 16.79 (P90; V1 Baseline: 16.61)
                </span>
              </div>
              <div className="p-3 rounded-xl bg-ivory-100/70 border border-ivory-200 font-mono text-[11px]">
                <span className="text-graphite-500 block">Evaluation:</span>
                <span className="text-teal-900 font-semibold">
                  {incident.confidence_tier === "actionable"
                    ? "Qualified for immediate analyst intervention"
                    : "Filtered to background noise / informational tier"}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Explainable Severity Score Breakdown Panel */}
      {incident.score_breakdown && (
        <div className="crystal-card p-6 shadow-crystal space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-ivory-200 pb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center border border-indigo-200">
                <Calculator className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-graphite-900">Score Breakdown &amp; Forensic Explainability</h2>
                  <div className="group relative">
                    <span className="cursor-help inline-flex items-center justify-center w-4 h-4 rounded-full bg-ivory-200 text-graphite-600 hover:bg-ivory-300 text-[10px] font-bold">
                      ?
                    </span>
                    <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-72 p-3 bg-graphite-950 text-white text-[11px] rounded-xl shadow-xl z-30 leading-relaxed border border-graphite-800">
                      <p className="font-bold text-ivory-100 mb-1">Scoring Methodology:</p>
                      <p className="font-mono text-[10px] text-teal-300 mb-1">
                        Severity = (Asset × 3) + (Event × 2) + ln(Alerts + 1)
                      </p>
                      <ul className="space-y-0.5 text-ivory-300 text-[10px]">
                        <li>• <strong>Asset (×3):</strong> High=3, Medium=2, Low=1</li>
                        <li>• <strong>Event (×2):</strong> PrivEsc=5, Exfil=3, Login/File=2, VPN=1</li>
                        <li>• <strong>Volume (×1):</strong> Natural log scaling dampens flood noise.</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-graphite-500">
                  Transparent mathematical breakdown showing exactly why this incident received a severity score of {incident.severity_score.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto font-mono text-xs bg-ivory-100 px-3 py-1.5 rounded-xl border border-ivory-300">
              <span className="text-graphite-500">Formula:</span>
              <span className="text-rose-700 font-semibold">{incident.score_breakdown.asset_component.toFixed(2)}</span>
              <span className="text-graphite-400">+</span>
              <span className="text-amber-700 font-semibold">{incident.score_breakdown.event_component.toFixed(2)}</span>
              <span className="text-graphite-400">+</span>
              <span className="text-indigo-700 font-semibold">{incident.score_breakdown.volume_component.toFixed(2)}</span>
              <span className="text-graphite-400">=</span>
              <span className="text-graphite-950 font-bold">{incident.severity_score.toFixed(2)}</span>
            </div>
          </div>

          {/* Plain-language explanation banner */}
          <div className="p-3.5 bg-ivory-100/70 border border-ivory-300/80 rounded-xl text-xs text-graphite-700 leading-relaxed">
            <span className="font-semibold text-graphite-900">Analyst Summary: </span>
            This incident scored <strong className="font-mono text-graphite-950">{incident.severity_score.toFixed(2)}</strong> &mdash;{" "}
            driven primarily by a{" "}
            <strong className="text-rose-700 font-semibold">
              {incident.score_breakdown.top_asset_factor || "critical asset"}
            </strong>{" "}
            contributing <span className="font-mono font-semibold text-graphite-950">+{incident.score_breakdown.asset_component.toFixed(2)} pts</span> and a{" "}
            <strong className="text-amber-700 font-semibold">
              {incident.score_breakdown.top_event_factor || "high-severity event"}
            </strong>{" "}
            contributing <span className="font-mono font-semibold text-graphite-950">+{incident.score_breakdown.event_component.toFixed(2)} pts</span>, with a smaller contribution of{" "}
            <span className="font-mono font-semibold text-graphite-950">+{incident.score_breakdown.volume_component.toFixed(2)} pts</span> from correlated alert volume ({incident.alert_count} alerts).
          </div>

          {/* 3 Component Breakdown Cards with Full Calculation Chain */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* 1. Asset Criticality */}
            <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-800">
                  Asset Criticality
                </span>
                <span className="text-xs font-mono font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded border border-rose-200">
                  Weight &times; 3
                </span>
              </div>
              <div className="text-2xl font-black text-rose-900 font-mono">
                +{incident.score_breakdown.asset_component.toFixed(2)}
              </div>
              <div className="text-[11px] text-graphite-600 space-y-1 font-mono pt-1 border-t border-rose-200/70">
                <div className="truncate">
                  Target: <strong className="text-graphite-900 font-semibold">{incident.score_breakdown.top_asset_factor || "N/A"}</strong>
                </div>
                <div>
                  Level: <strong className="text-graphite-900">{incident.score_breakdown.asset_raw_level || (incident.score_breakdown.asset_component === 9 ? "HIGH" : incident.score_breakdown.asset_component === 6 ? "MEDIUM" : "LOW")}</strong>
                </div>
                <div className="text-graphite-500 text-[10px]">
                  Lookup: HIGH=3, MED=2, LOW=1 &rarr; <span className="text-graphite-900 font-semibold">{incident.score_breakdown.asset_raw_score ?? (incident.score_breakdown.asset_component === 9 ? 3 : 2)}</span>
                </div>
                <div className="text-rose-800 font-bold">
                  Calculation: {incident.score_breakdown.asset_raw_score ?? (incident.score_breakdown.asset_component === 9 ? 3 : 2)} &times; 3 = +{incident.score_breakdown.asset_component.toFixed(2)}
                </div>
              </div>
            </div>

            {/* 2. Event Severity */}
            <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-800">
                  Event Severity
                </span>
                <span className="text-xs font-mono font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded border border-amber-200">
                  Weight &times; 2
                </span>
              </div>
              <div className="text-2xl font-black text-amber-900 font-mono">
                +{incident.score_breakdown.event_component.toFixed(2)}
              </div>
              <div className="text-[11px] text-graphite-600 space-y-1 font-mono pt-1 border-t border-amber-200/70">
                <div className="truncate">
                  Action: <strong className="text-graphite-900 font-semibold">{incident.score_breakdown.top_event_factor || incident.score_breakdown.event_type_used || "N/A"}</strong>
                </div>
                <div>
                  Severity Lookup: <strong className="text-graphite-900">{incident.score_breakdown.event_raw_score ?? Math.round(incident.score_breakdown.event_component / 2)}</strong>
                </div>
                <div className="text-graphite-500 text-[10px]">
                  PrivEsc=5, Exfil=3, Login/File=2, VPN=1
                </div>
                <div className="text-amber-800 font-bold">
                  Calculation: {incident.score_breakdown.event_raw_score ?? Math.round(incident.score_breakdown.event_component / 2)} &times; 2 = +{incident.score_breakdown.event_component.toFixed(2)}
                </div>
              </div>
            </div>

            {/* 3. Alert Volume */}
            <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-800">
                  Alert Volume Scaling
                </span>
                <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-100 px-2 py-0.5 rounded border border-indigo-200">
                  ln(N+1) &times; 1
                </span>
              </div>
              <div className="text-2xl font-black text-indigo-900 font-mono">
                +{incident.score_breakdown.volume_component.toFixed(2)}
              </div>
              <div className="text-[11px] text-graphite-600 space-y-1 font-mono pt-1 border-t border-indigo-200/70">
                <div>
                  Correlated Alerts: <strong className="text-graphite-900 font-semibold">{incident.score_breakdown.alert_count_used || incident.alert_count}</strong>
                </div>
                <div className="text-graphite-500 text-[10px]">
                  Formula: ln({(incident.score_breakdown.alert_count_used || incident.alert_count)} + 1)
                </div>
                <div className="text-indigo-800 font-bold">
                  Calculation: ln({(incident.score_breakdown.alert_count_used || incident.alert_count) + 1}) &times; 1 = +{incident.score_breakdown.volume_component.toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Incident Brief Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-200">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-graphite-950">AI Intelligence Brief</h2>
              <p className="text-xs text-graphite-500">
                Synthesized by Groq LLM with full alert correlation and MITRE context
              </p>
            </div>
          </div>

          {brief && brief.summary_text && !brief.summary_text.includes("[AI summary unavailable") && (
            <span className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-xl font-medium flex items-center gap-1.5 shadow-2xs">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Groq AI Brief Verified
            </span>
          )}
        </div>

        <BriefDisplay
          brief={brief}
          incidentId={incident.incident_id}
          onGenerateBrief={handleGenerateBrief}
        />
      </div>

      {/* Traceable Source Alerts Table */}
      <div className="crystal-card shadow-crystal overflow-hidden">
        <div className="p-6 border-b border-ivory-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-ivory-100 text-graphite-700 flex items-center justify-center border border-ivory-300">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-graphite-950">
                Traceable Correlated Alerts
              </h2>
              <p className="text-xs text-graphite-500">
                All {alerts.length} underlying raw security alerts clustered into this incident
              </p>
            </div>
          </div>

          <span className="text-xs font-semibold px-3 py-1 bg-ivory-100 text-graphite-700 rounded-full border border-ivory-300 self-start sm:self-auto font-mono">
            {alerts.length} alerts linked
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-ivory-100/60 border-b border-ivory-200 text-[11px] font-bold uppercase tracking-wider text-graphite-500 font-mono">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Event Type</th>
                <th className="py-3 px-4">Criticality</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Source IP</th>
                <th className="py-3 px-4">Target Asset</th>
                <th className="py-3 px-4">Raw Log Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ivory-200/80 text-xs">
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-graphite-400">
                    No source alerts linked to this incident.
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr
                    key={alert.alert_id}
                    onClick={() => setSelectedAlert(alert)}
                    className="hover:bg-teal-50/30 transition-colors cursor-pointer group"
                  >
                    <td className="py-3.5 px-4 font-mono text-graphite-500 whitespace-nowrap">
                      {new Date(alert.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-graphite-900 whitespace-nowrap">
                      {alert.event_type}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
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
                    <td className="py-3.5 px-4 font-medium text-graphite-700 whitespace-nowrap font-mono">
                      {alert.username || "—"}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-graphite-600 whitespace-nowrap">
                      {alert.source_ip || "—"}
                    </td>
                    <td className="py-3.5 px-4 text-graphite-700 whitespace-nowrap">
                      <span className="font-mono text-[11px] bg-ivory-100 border border-ivory-200 px-2 py-0.5 rounded text-graphite-800">
                        {alert.target_asset || "—"}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-graphite-600 max-w-xs md:max-w-md truncate font-mono text-[11px]">
                      {alert.raw_message}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 bg-graphite-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="crystal-card max-w-xl w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150 bg-white">
            <div className="flex items-center justify-between border-b border-ivory-200 pb-3">
              <h3 className="text-base font-bold text-graphite-950 flex items-center gap-2">
                <Info className="w-4 h-4 text-teal-700" />
                Raw Telemetry Alert Detail
              </h3>
              <button
                onClick={() => setSelectedAlert(null)}
                className="text-graphite-400 hover:text-graphite-700 font-bold p-1 rounded-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3 bg-ivory-100/70 p-3.5 rounded-xl border border-ivory-200">
                <div>
                  <span className="text-graphite-400 block font-semibold text-[10px] uppercase font-mono">Alert ID</span>
                  <span className="font-mono text-graphite-800 text-[11px]">{selectedAlert.alert_id}</span>
                </div>
                <div>
                  <span className="text-graphite-400 block font-semibold text-[10px] uppercase font-mono">Event Type</span>
                  <span className="font-medium text-graphite-900">{selectedAlert.event_type}</span>
                </div>
                <div>
                  <span className="text-graphite-400 block font-semibold text-[10px] uppercase font-mono">Asset Criticality</span>
                  <span className="font-bold uppercase text-graphite-800 font-mono">
                    {selectedAlert.asset_criticality}
                  </span>
                </div>
                <div>
                  <span className="text-graphite-400 block font-semibold text-[10px] uppercase font-mono">Source IP</span>
                  <span className="font-mono text-graphite-800">{selectedAlert.source_ip || "N/A"}</span>
                </div>
                <div>
                  <span className="text-graphite-400 block font-semibold text-[10px] uppercase font-mono">User</span>
                  <span className="font-medium text-graphite-800 font-mono">{selectedAlert.username || "N/A"}</span>
                </div>
              </div>

              <div>
                <span className="text-graphite-400 block font-semibold mb-1 text-[10px] uppercase font-mono">Target Asset</span>
                <span className="font-mono bg-ivory-100 border border-ivory-200 text-graphite-800 px-2 py-1 rounded block">
                  {selectedAlert.target_asset}
                </span>
              </div>

              <div>
                <span className="text-graphite-400 block font-semibold mb-1 text-[10px] uppercase font-mono">Timestamp</span>
                <span className="font-mono text-graphite-700">{selectedAlert.timestamp}</span>
              </div>

              <div>
                <span className="text-graphite-400 block font-semibold mb-1 text-[10px] uppercase font-mono">Raw Log Message</span>
                <pre className="bg-graphite-950 text-teal-300 p-3.5 rounded-xl font-mono text-[11px] whitespace-pre-wrap break-all shadow-inner">
                  {selectedAlert.raw_message}
                </pre>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedAlert(null)}
                className="tactile-button px-4 py-2 bg-graphite-950 hover:bg-graphite-900 text-white rounded-xl text-xs font-semibold shadow-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
