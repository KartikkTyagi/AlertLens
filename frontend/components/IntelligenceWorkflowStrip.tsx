"use client";

import React from "react";
import { ArrowRight, Bell, Network, Gauge, ShieldAlert, CheckCircle2 } from "lucide-react";

export const IntelligenceWorkflowStrip: React.FC = () => {
  const steps = [
    {
      id: "1",
      number: "01",
      title: "SIEM Telemetry Ingestion",
      detail: "3,000 Raw Alerts",
      desc: "Heterogeneous noisy log flood (V1: 2,569)",
      icon: Bell,
      color: "border-slate-300 text-slate-700 bg-white",
      pill: "High Volume Noise",
      pillColor: "bg-slate-100 text-slate-700 border-slate-200",
    },
    {
      id: "2",
      number: "02",
      title: "Semantic Graph Correlation",
      detail: "543 Graph Clusters",
      desc: "Embedding similarity & entity graphs (V1: 490)",
      icon: Network,
      color: "border-teal-300 text-teal-700 bg-teal-50/50",
      pill: "Anti-Percolation",
      pillColor: "bg-teal-50 text-teal-700 border-teal-200",
    },
    {
      id: "3",
      number: "03",
      title: "Dynamic Severity Scoring",
      detail: "P90 Threshold: 16.79",
      desc: "Asset × 3 + Event × 2 + ln(Vol) [V1: 16.61]",
      icon: Gauge,
      color: "border-amber-300 text-amber-700 bg-amber-50/50",
      pill: "Explainable ML",
      pillColor: "bg-amber-50 text-amber-700 border-amber-200",
    },
    {
      id: "4",
      number: "04",
      title: "Behavioral MITRE Context",
      detail: "Kill-Chain Progression",
      desc: "Multi-stage attack sequence",
      icon: ShieldAlert,
      color: "border-purple-300 text-purple-700 bg-purple-50/50",
      pill: "Attack Context",
      pillColor: "bg-purple-50 text-purple-700 border-purple-200",
    },
    {
      id: "5",
      number: "05",
      title: "Actionable SOC Triage",
      detail: "113 Priority Threats",
      desc: "LLM incident briefs & audit trace (V1: 91)",
      icon: CheckCircle2,
      color: "border-emerald-300 text-emerald-700 bg-emerald-50/50",
      pill: "92.5% Labor Saved",
      pillColor: "bg-emerald-50 text-emerald-800 border-emerald-200 font-bold",
    },
  ];

  return (
    <div className="rounded-2xl border border-ivory-300 bg-white/80 backdrop-blur-md p-6 shadow-crystal">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-5 pb-3 border-b border-ivory-200">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-graphite-900 flex items-center gap-2">
            <span>Autonomous Intelligence &amp; Triage Pipeline</span>
          </h3>
          <p className="text-xs text-graphite-500">
            How AlertLens compresses 3,000 raw alerts into 113 actionable incidents with zero manual tuning (V1 Baseline: 2,569 alerts &rarr; 91 actionable)
          </p>
        </div>
        <span className="text-[11px] font-mono text-teal-700 bg-teal-50 border border-teal-200 px-2.5 py-0.5 rounded-full font-semibold self-start sm:self-auto">
          100% Ground-Truth Threat Recall
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3 relative">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={step.id}
              className="relative p-4 rounded-xl border border-ivory-200 bg-ivory-50/40 hover:bg-white hover:border-ivory-300 transition-all duration-200 flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-graphite-400">
                    STAGE {step.number}
                  </span>
                  <div className={`p-1.5 rounded-lg border ${step.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                </div>

                <h4 className="text-xs font-bold text-graphite-900 leading-snug">
                  {step.title}
                </h4>
                <div className="text-xs font-extrabold text-graphite-800 font-mono mt-0.5">
                  {step.detail}
                </div>
                <p className="text-[11px] text-graphite-500 mt-1 leading-relaxed">
                  {step.desc}
                </p>
              </div>

              <div className="pt-2 border-t border-ivory-200/60">
                <span className={`inline-block text-[10px] uppercase font-semibold px-2 py-0.5 rounded border ${step.pillColor}`}>
                  {step.pill}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
