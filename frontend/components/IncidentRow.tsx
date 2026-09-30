"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight, Layers, Clock } from "lucide-react";
import { Incident } from "@/types";
import { SeverityBadge } from "./SeverityBadge";
import { MitreBadge } from "./MitreBadge";
import { GlossaryTooltip } from "./GlossaryTooltip";

interface IncidentRowProps {
  incident: Incident;
  isHighlighted?: boolean;
}

export const IncidentRow: React.FC<IncidentRowProps> = ({ incident, isHighlighted = false }) => {
  const formattedDate = new Date(incident.created_at).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Link
      href={`/incidents/${incident.incident_id}`}
      className={`group block rounded-2xl border p-4 sm:p-5 transition-all duration-200 ${
        isHighlighted
          ? "border-teal-500 bg-teal-50/90 shadow-crystal-teal ring-2 ring-teal-500/50 animate-pulse"
          : "bg-white/85 hover:bg-white border-ivory-300/80 hover:border-ivory-400 shadow-crystal hover:shadow-crystal-hover"
      }`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Left: Rank, Severity & Identifiers */}
        <div className="flex items-center gap-3.5 flex-wrap">
          <div className="w-10 h-10 rounded-xl bg-ivory-100 border border-ivory-300 flex items-center justify-center font-mono font-bold text-graphite-800 text-sm group-hover:bg-teal-50 group-hover:border-teal-300 group-hover:text-teal-800 transition-colors shadow-2xs">
            #{incident.severity_rank}
          </div>

          <div className="flex flex-col gap-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-graphite-900">
                {incident.incident_id.slice(0, 8)}...
              </span>
              <SeverityBadge score={incident.severity_score} />
              <MitreBadge tag={incident.mitre_tag} techniqueName={incident.mitre_technique_name} />
              
              {incident.attack_progression && incident.attack_progression !== "None (Isolated Activity)" && (
                <span
                  title={incident.progression_detail || incident.attack_progression}
                  className="inline-flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-purple-50 text-purple-800 border border-purple-200"
                >
                  <span>⚡ {incident.attack_progression}</span>
                </span>
              )}

              {incident.correlation_confidence !== undefined && incident.correlation_confidence !== null && (
                <span
                  title={incident.confidence_reason ? `Graph Cohesion: ${incident.confidence_reason}` : "Graph Cohesion"}
                  className="inline-flex items-center text-[10px] font-mono font-semibold px-2 py-0.5 rounded-md bg-ivory-100 text-graphite-600 border border-ivory-200"
                >
                  {Math.round(incident.correlation_confidence * 100)}% Cohesion
                </span>
              )}

              {incident.confidence_tier === "informational" && (
                <span className="inline-flex items-center text-[10px] font-mono font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200">
                  Informational
                </span>
              )}

              {incident.acknowledged ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                  <span>✓ Acknowledged</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium uppercase tracking-wider px-2 py-0.5 rounded-md bg-ivory-100 text-graphite-500 border border-ivory-200">
                  <span>Pending Triage</span>
                </span>
              )}
            </div>

            <div className="flex items-center gap-3 text-xs text-graphite-500">
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-teal-600" />
                <strong className="text-graphite-800 font-bold">{incident.alert_count}</strong>{" "}
                correlated alert{incident.alert_count === 1 ? "" : "s"}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-graphite-400" />
                <span>{formattedDate}</span>
              </span>
            </div>
          </div>
        </div>

        {/* Right: Score and Action Link */}
        <div className="flex items-center justify-between sm:justify-end gap-5 pt-2 sm:pt-0 border-t sm:border-t-0 border-ivory-200">
          <div className="text-right">
            <div className="text-[10px] font-mono uppercase tracking-wider text-graphite-400 font-semibold inline-flex items-center gap-1 justify-end">
              Severity Score
              <span onClick={(e) => e.stopPropagation()}>
                <GlossaryTooltip term="severity_score" position="left" />
              </span>
            </div>
            <div className="text-xl sm:text-2xl font-black text-graphite-950 font-mono">
              {incident.severity_score.toFixed(2)}
            </div>
          </div>

          <div className="w-8 h-8 rounded-xl bg-ivory-50 border border-ivory-200 flex items-center justify-center text-graphite-400 group-hover:bg-teal-600 group-hover:text-white group-hover:border-teal-600 transition-all shadow-2xs">
            <ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
          </div>
        </div>
      </div>
    </Link>
  );
};
