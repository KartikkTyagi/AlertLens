"use client";

import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { Incident } from "@/types";

import { GlossaryTooltip } from "@/components/GlossaryTooltip";

interface SeverityChartProps {
  incidents: Incident[];
}

export const SeverityChart: React.FC<SeverityChartProps> = ({ incidents }) => {
  const chartData = incidents.slice(0, 15).map((inc) => ({
    name: `#${inc.severity_rank}`,
    incident_id: inc.incident_id,
    score: inc.severity_score,
    alerts: inc.alert_count,
    mitre: inc.mitre_tag || "Not mapped",
    mitre_name: inc.mitre_technique_name,
    breakdown: inc.score_breakdown,
  }));

  const getBarColor = (score: number) => {
    if (score >= 18.0) return "#f43f5e"; // rose-500
    if (score >= 15.0) return "#f59e0b"; // amber-500
    if (score >= 12.0) return "#eab308"; // yellow-500
    return "#10b981"; // emerald-500
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const bd = data.breakdown;
      const assetLevel = bd?.asset_raw_level || (bd?.asset_component === 9 ? "HIGH" : bd?.asset_component === 6 ? "MEDIUM" : "LOW");
      const assetScore = bd?.asset_raw_score ?? (bd?.asset_component === 9 ? 3 : bd?.asset_component === 6 ? 2 : 1);
      const eventType = bd?.event_type_used || bd?.top_event_factor?.split(" ")[0] || "event";
      const eventScore = bd?.event_raw_score ?? Math.round((bd?.event_component || 2) / 2);
      const alertCount = bd?.alert_count_used ?? data.alerts;

      return (
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xl text-xs font-sans max-w-sm">
          <p className="font-bold text-slate-900 mb-2 flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-sm font-extrabold">Incident {data.name}</span>
            <span className="font-mono font-normal text-slate-400 text-[10px]">
              {data.incident_id.slice(0, 8)}...
            </span>
          </p>

          <div className="space-y-1.5 text-slate-600 pb-2.5 border-b border-slate-100">
            <div className="flex justify-between items-center">
              <span className="inline-flex items-center gap-1 font-medium">
                Severity Score
                <GlossaryTooltip term="severity_score" position="right" />
              </span>
              <strong className="text-slate-900 font-mono text-base font-black">{data.score.toFixed(2)}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span>Correlated Alerts:</span>
              <strong className="text-slate-900 font-semibold">{data.alerts}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="inline-flex items-center gap-1">
                MITRE Technique:
                <GlossaryTooltip term="mitre_technique" position="right" />
              </span>
              {data.mitre === "Not mapped" ? (
                <span className="text-slate-400 font-sans text-xs">Not mapped</span>
              ) : (
                <strong className="text-indigo-600 font-mono font-bold">
                  {data.mitre}{data.mitre_name ? ` (${data.mitre_name})` : ""}
                </strong>
              )}
            </div>
          </div>

          {bd && (
            <div className="mt-2.5 pt-1 text-[11px]">
              <div className="font-bold text-slate-800 text-xs mb-2 flex items-center justify-between">
                <span>Calculation Chain (Full Breakdown)</span>
                <span className="text-[10px] text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded font-mono font-semibold">
                  {bd.asset_component?.toFixed(2)} + {bd.event_component?.toFixed(2)} + {bd.volume_component?.toFixed(2)} = {data.score.toFixed(2)}
                </span>
              </div>

              <div className="space-y-2 bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 text-[10px]">
                {/* Asset Criticality Chain */}
                <div className="space-y-0.5 border-b border-slate-200/60 pb-1.5">
                  <div className="flex justify-between items-center text-slate-800">
                    <span className="font-bold text-rose-700">1. Asset Criticality (×3)</span>
                    <span className="font-mono font-black text-rose-700 text-[11px]">
                      {assetScore} × 3 = +{bd.asset_component?.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-slate-600 font-mono text-[9px]">
                    Target: {bd.top_asset_factor || "N/A"} → Level: <strong className="text-slate-900">{assetLevel}</strong>
                  </div>
                  <div className="text-slate-500 text-[9px]">
                    Raw Lookup: HIGH=3, MED=2, LOW=1 → <span className="font-semibold text-slate-800">{assetLevel} = {assetScore}</span>
                  </div>
                </div>

                {/* Event Severity Chain */}
                <div className="space-y-0.5 border-b border-slate-200/60 pb-1.5">
                  <div className="flex justify-between items-center text-slate-800">
                    <span className="font-bold text-amber-700">2. Event Severity (×2)</span>
                    <span className="font-mono font-black text-amber-700 text-[11px]">
                      {eventScore} × 2 = +{bd.event_component?.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-slate-600 font-mono text-[9px]">
                    Action: {bd.top_event_factor || eventType} → Raw Severity: <strong className="text-slate-900">{eventScore}</strong>
                  </div>
                  <div className="text-slate-500 text-[9px]">
                    PrivEsc=5, Exfil=3, Login/File=2, VPN=1
                  </div>
                </div>

                {/* Alert Volume Chain */}
                <div className="space-y-0.5">
                  <div className="flex justify-between items-center text-slate-800">
                    <span className="font-bold text-indigo-700">3. Logarithmic Alert Volume (×1)</span>
                    <span className="font-mono font-black text-indigo-700 text-[11px]">
                      +{bd.volume_component?.toFixed(2)}
                    </span>
                  </div>
                  <div className="text-slate-600 font-mono text-[9px]">
                    Formula: ln({alertCount} + 1) = ln({alertCount + 1}) = {bd.volume_component?.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-sm">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
              Severity Score Distribution (Top 15 Incidents)
              <GlossaryTooltip term="severity_score" position="bottom" />
            </h3>
            <div className="group relative">
              <span className="cursor-help inline-flex items-center justify-center w-4 h-4 rounded-full bg-slate-100 text-slate-500 hover:bg-slate-200 text-[10px] font-bold">
                ?
              </span>
              <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block w-80 p-3 bg-slate-900 text-white text-[11px] rounded-lg shadow-xl z-30 leading-relaxed">
                <p className="font-bold text-slate-100 mb-1">Scoring Methodology &amp; Lookup Table:</p>
                <p className="font-mono text-[10px] text-teal-300 mb-1.5">
                  Score = (Asset Raw × 3) + (Event Raw × 2) + ln(Alerts + 1)
                </p>
                <ul className="space-y-0.5 text-slate-300 text-[10px]">
                  <li>• <strong>Asset Lookup (×3):</strong> HIGH=3, MEDIUM=2, LOW=1</li>
                  <li>• <strong>Event Lookup (×2):</strong> privilege_escalation=5, file_download=3, failed_login=2, successful_login=2, file_access=2, vpn_connect=1, password_change=1</li>
                  <li>• <strong>Volume (×1):</strong> Natural log ln(N+1) scaling prevents noise inundation.</li>
                </ul>
              </div>
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Formula: (Asset × 3) + (Event × 2) + ln(Vol + 1) &bull; Hover bar for full transparent calculation chain
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            Critical (&ge;18)
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            High (&ge;15)
          </span>
          <span className="flex items-center gap-1.5 text-slate-600">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            Medium / Low
          </span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis
              dataKey="name"
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
              tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
            />
            <YAxis
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
              tick={{ fill: "#64748b", fontSize: 11 }}
              domain={[0, 25]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="score" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
