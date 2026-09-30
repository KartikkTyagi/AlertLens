"use client";

import React from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ArrowRight,
  Layers,
  Clock,
  Activity,
  Network,
  CheckCircle,
  ExternalLink,
  ChevronRight,
  Server,
  Zap,
} from "lucide-react";
import { Incident } from "@/types";
import { SeverityBadge } from "./SeverityBadge";
import { MitreBadge } from "./MitreBadge";
import { GlossaryTooltip } from "./GlossaryTooltip";

interface PriorityIncidentCardProps {
  incident: Incident;
}

export const PriorityIncidentCard: React.FC<PriorityIncidentCardProps> = ({ incident }) => {
  const formattedDate = new Date(incident.created_at).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  const topAsset = incident.score_breakdown?.top_asset_factor || "finance-db-01 (high criticality)";

  return (
    <div className="relative rounded-2xl border border-ivory-300/90 bg-gradient-to-br from-white/95 via-ivory-50/90 to-teal-50/20 backdrop-blur-md p-6 shadow-crystal hover:shadow-crystal-hover transition-all duration-300 group overflow-hidden">
      {/* Subtle Luminous Ambient Accent Glow */}
      <div className="absolute -top-12 -right-12 w-48 h-48 bg-gradient-to-bl from-teal-500/10 via-amber-500/5 to-transparent rounded-full blur-2xl pointer-events-none" />
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-teal-600/50 to-transparent" />

      {/* Card Header Tag Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-ivory-200">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-graphite-900 text-ivory-50 text-xs font-mono font-bold tracking-wider shadow-xs">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>PRIORITY THREAT · RANK #{incident.severity_rank}</span>
          </span>

          <SeverityBadge score={incident.severity_score} />
          <MitreBadge tag={incident.mitre_tag} techniqueName={incident.mitre_technique_name} showFullName={true} />
        </div>

        <div className="flex items-center gap-2">
          {incident.acknowledged ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              <span>Acknowledged by {incident.acknowledged_by}</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 text-xs font-bold animate-pulse">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-600" />
              <span>Immediate Attention Required</span>
            </span>
          )}
        </div>
      </div>

      {/* Main Body Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-5">
        {/* Left Column: Big Score & Target Asset */}
        <div className="lg:col-span-5 space-y-3">
          <div className="flex items-baseline gap-3">
            <span className="text-4xl sm:text-5xl font-black text-graphite-900 tracking-tight font-mono">
              {incident.severity_score.toFixed(2)}
            </span>
            <div>
              <span className="text-xs uppercase tracking-wider font-bold text-graphite-500 block">
                Composite Severity
              </span>
              <span className="text-[11px] font-mono text-teal-700 font-semibold">
                Extreme Risk (P90 &ge; 16.79)
              </span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-white/80 border border-ivory-200 space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-semibold text-graphite-600">
              <Server className="w-3.5 h-3.5 text-rose-600" />
              <span>Target Crown-Jewel Asset</span>
            </div>
            <p className="text-sm font-bold text-graphite-900 font-mono truncate">
              {topAsset}
            </p>
          </div>
        </div>

        {/* Middle Column: Behavioral Intelligence & Cohesion */}
        <div className="lg:col-span-4 space-y-3 text-xs">
          <div className="p-3 rounded-xl bg-white/80 border border-ivory-200 space-y-1">
            <div className="flex items-center justify-between text-graphite-500 font-semibold">
              <span className="flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-purple-600" />
                <span>Attack Progression:</span>
              </span>
              <span className="text-purple-700 font-bold uppercase tracking-wide text-[10px]">
                {incident.attack_progression}
              </span>
            </div>
            <p className="text-[11px] text-graphite-600 font-mono truncate">
              {incident.progression_detail || "Multi-stage intrusion path"}
            </p>
          </div>

          <div className="p-3 rounded-xl bg-white/80 border border-ivory-200 space-y-1">
            <div className="flex items-center justify-between text-graphite-500 font-semibold">
              <span className="flex items-center gap-1.5">
                <Network className="w-3.5 h-3.5 text-teal-600" />
                <span>Evidence Cohesion:</span>
              </span>
              <span className="text-teal-700 font-mono font-bold">
                {Math.round((incident.correlation_confidence ?? 0.75) * 100)}% Match
              </span>
            </div>
            <p className="text-[11px] text-graphite-600 truncate">
              {incident.confidence_reason || "Multi-entity graph linkage"}
            </p>
          </div>
        </div>

        {/* Right Column: Alert Count & CTA */}
        <div className="lg:col-span-3 flex flex-col justify-between space-y-4">
          <div className="space-y-1 text-right">
            <div className="text-xs text-graphite-500 flex items-center justify-end gap-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-600" />
              <strong className="text-graphite-900 font-bold text-sm">{incident.alert_count}</strong>
              <span>correlated alerts</span>
            </div>
            <div className="text-[11px] text-graphite-400 flex items-center justify-end gap-1">
              <Clock className="w-3 h-3 text-graphite-400" />
              <span>{formattedDate}</span>
            </div>
          </div>

          <Link
            href={`/incidents/${incident.incident_id}`}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold tracking-wide tactile-button"
          >
            <span>Open Investigation</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>
    </div>
  );
};
