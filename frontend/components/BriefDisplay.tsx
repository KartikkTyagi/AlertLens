"use client";

import React, { useState } from "react";
import {
  FileText,
  ShieldAlert,
  CheckCircle2,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Cpu,
  ArrowRight,
  Zap,
} from "lucide-react";
import { IncidentBrief } from "@/types";

interface BriefDisplayProps {
  brief?: IncidentBrief | null;
  summaryText?: string | null;
  incidentId?: string;
  onGenerateBrief?: () => Promise<void>;
}

interface ParsedSection {
  title: string;
  body: string;
}

export const BriefDisplay: React.FC<BriefDisplayProps> = ({
  brief,
  summaryText,
  incidentId,
  onGenerateBrief,
}) => {
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const effectiveText = brief?.summary_text || summaryText || "";

  const handleGenerate = async () => {
    if (!onGenerateBrief) return;
    try {
      setGenerating(true);
      setGenerateError(null);
      await onGenerateBrief();
    } catch (err: any) {
      setGenerateError(err?.message || "Failed to generate AI brief with Groq");
    } finally {
      setGenerating(false);
    }
  };

  // Parse structured markdown sections like "### What Happened", etc.
  const parseSections = (text: string): ParsedSection[] => {
    if (!text || text.includes("[AI summary unavailable")) {
      return [];
    }

    const sections: ParsedSection[] = [];
    const lines = text.split("\n");
    let currentTitle = "";
    let currentBodyLines: string[] = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (
        trimmed.startsWith("###") ||
        trimmed.startsWith("##") ||
        trimmed.startsWith("**1.") ||
        trimmed.startsWith("**2.") ||
        trimmed.startsWith("**3.")
      ) {
        if (currentTitle) {
          sections.push({
            title: currentTitle,
            body: currentBodyLines.join("\n").trim(),
          });
          currentBodyLines = [];
        }
        currentTitle = trimmed
          .replace(/^#+\s*/, "")
          .replace(/^\*\*/, "")
          .replace(/\*\*.*$/, "")
          .replace(/:\s*$/, "")
          .trim();
      } else if (currentTitle) {
        currentBodyLines.push(line);
      }
    }

    if (currentTitle && currentBodyLines.length > 0) {
      sections.push({
        title: currentTitle,
        body: currentBodyLines.join("\n").trim(),
      });
    }

    return sections;
  };

  const sections = parseSections(effectiveText);

  // State B: Generation in Progress
  if (generating) {
    return (
      <div className="rounded-2xl border border-teal-200/80 bg-white/90 backdrop-blur-md p-8 shadow-crystal text-center space-y-4">
        <div className="w-12 h-12 border-3 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <div>
          <h4 className="font-bold text-base text-graphite-900">
            Synthesizing Forensic Intelligence Brief...
          </h4>
          <p className="text-xs text-graphite-500 mt-1">
            Correlating alert timeline and querying Groq LLM across MITRE technique context...
          </p>
        </div>
      </div>
    );
  }

  // State C: Generation Failed (explicit error)
  if (generateError) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-white/95 backdrop-blur-md p-6 shadow-crystal flex flex-col sm:flex-row items-start justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-2 rounded-xl bg-rose-50 text-rose-600 border border-rose-100">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-rose-950">
              AI Brief Generation Failed
            </h4>
            <p className="mt-1 text-xs text-rose-700 leading-relaxed">
              {generateError}
            </p>
          </div>
        </div>

        {onGenerateBrief && (
          <button
            onClick={handleGenerate}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-all tactile-button shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Generation</span>
          </button>
        )}
      </div>
    );
  }

  // State D: AI Provider Unavailable (fallback summary present in DB)
  if (effectiveText.includes("[AI summary unavailable")) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-white/90 backdrop-blur-md p-6 shadow-crystal flex flex-col sm:flex-row items-start justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-2 rounded-xl bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-graphite-900">
              AI Provider Offline During Seeding
            </h4>
            <p className="mt-1 text-xs text-graphite-600 leading-relaxed">
              This incident was processed while the LLM provider was unreachable. You can trigger an on-demand synthesis now using the active Groq connection.
            </p>
          </div>
        </div>

        {onGenerateBrief && (
          <button
            onClick={handleGenerate}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition-all tactile-button shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate Brief Now</span>
          </button>
        )}
      </div>
    );
  }

  // State E: No Brief Generated Yet (null brief)
  if (!effectiveText || sections.length === 0) {
    return (
      <div className="rounded-2xl border border-ivory-300 bg-white/90 backdrop-blur-md p-6 shadow-crystal flex flex-col sm:flex-row items-start justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-2 rounded-xl bg-ivory-100 text-graphite-600 border border-ivory-200">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-sm text-graphite-900">
              No Brief Generated Yet
            </h4>
            <p className="mt-1 text-xs text-graphite-500 leading-relaxed">
              This incident has not had an AI forensic brief synthesized. Click below to generate an automated executive triage brief using Groq.
            </p>
          </div>
        </div>

        {onGenerateBrief && (
          <button
            onClick={handleGenerate}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition-all tactile-button shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Generate AI Brief</span>
          </button>
        )}
      </div>
    );
  }

  // State A: Brief Available & Validated (Render the 3 structured sections)
  const getSectionMeta = (title: string, index: number) => {
    const lower = title.toLowerCase();
    if (lower.includes("happened") || index === 0) {
      return {
        icon: FileText,
        badgeText: "Attack Synopsis",
        containerClass: "border-ivory-300/80 bg-gradient-to-br from-white via-ivory-25 to-slate-50/50",
        headerClass: "text-graphite-950",
        iconClass: "text-teal-700 bg-teal-50 border-teal-200",
        highlight: "border-l-4 border-l-teal-600",
      };
    }
    if (lower.includes("matters") || lower.includes("why") || index === 1) {
      return {
        icon: ShieldAlert,
        badgeText: "Threat Context & Risk",
        containerClass: "border-ivory-300/80 bg-gradient-to-br from-white via-ivory-25 to-rose-50/30",
        headerClass: "text-graphite-950",
        iconClass: "text-rose-700 bg-rose-50 border-rose-200",
        highlight: "border-l-4 border-l-rose-500",
      };
    }
    return {
      icon: CheckCircle2,
      badgeText: "Recommended Next Steps",
      containerClass: "border-ivory-300/80 bg-gradient-to-br from-white via-ivory-25 to-emerald-50/30",
      headerClass: "text-graphite-950",
      iconClass: "text-emerald-700 bg-emerald-50 border-emerald-200",
      highlight: "border-l-4 border-l-emerald-600",
    };
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sections.map((sec, idx) => {
          const meta = getSectionMeta(sec.title, idx);
          const Icon = meta.icon;

          return (
            <div
              key={idx}
              className={`rounded-2xl border p-6 shadow-crystal hover:shadow-crystal-hover transition-all duration-200 flex flex-col justify-between ${meta.containerClass} ${meta.highlight}`}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2 rounded-xl border ${meta.iconClass}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] uppercase tracking-wider font-mono font-bold px-2 py-0.5 rounded-full bg-white border border-ivory-300 text-graphite-600 shadow-2xs">
                    {meta.badgeText}
                  </span>
                </div>

                <h3 className={`text-base font-bold tracking-tight mb-2.5 ${meta.headerClass}`}>
                  {sec.title}
                </h3>

                <p className="text-graphite-700 text-xs sm:text-sm leading-relaxed whitespace-pre-line font-sans">
                  {sec.body}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
