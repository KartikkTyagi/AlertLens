"use client";

import React, { useState } from "react";
import { HelpCircle } from "lucide-react";

export type GlossaryTerm =
  | "severity_score"
  | "confidence_tier"
  | "precision"
  | "recall"
  | "mitre_technique";

interface GlossaryDefinition {
  title: string;
  definition: string;
}

export const GLOSSARY_DEFINITIONS: Record<GlossaryTerm, GlossaryDefinition> = {
  severity_score: {
    title: "Severity Score",
    definition:
      "A composite risk number (0-25+) combining how critical the targeted asset is, how dangerous the observed behavior is, and how many alerts are involved — used to rank which incidents need attention first.",
  },
  confidence_tier: {
    title: "Confidence Tier (Actionable / Informational)",
    definition:
      "Actionable means this correlated cluster matches a known attack pattern or meets the P90 severity risk threshold — these need analyst review. Informational means the correlation is real but doesn't show clear attack signals — likely background noise, kept visible for transparency but not prioritized.",
  },
  precision: {
    title: "Precision",
    definition:
      "Of the alerts grouped into this incident, the fraction that are confirmed to be part of the same real attack (measured against known planted test scenarios) — lower precision means some unrelated noise got swept in alongside the real signal.",
  },
  recall: {
    title: "Recall",
    definition:
      "Of a real attack's actual alerts, the fraction the pipeline successfully grouped together into one incident, rather than missing or splitting them apart.",
  },
  mitre_technique: {
    title: "MITRE ATT&CK Technique",
    definition:
      "A code (e.g., T1110) from a public, industry-standard catalog of known attacker behaviors — used to describe which real-world attack pattern this incident's alert pattern most closely resembles. Not every incident matches a known pattern; those are left untagged rather than guessed.",
  },
};

interface GlossaryTooltipProps {
  term: GlossaryTerm;
  className?: string;
  iconClassName?: string;
  position?: "top" | "bottom" | "left" | "right";
}

export const GlossaryTooltip: React.FC<GlossaryTooltipProps> = ({
  term,
  className = "",
  iconClassName = "w-3.5 h-3.5 text-slate-400 hover:text-teal-600 transition-colors",
  position = "top",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const entry = GLOSSARY_DEFINITIONS[term];

  if (!entry) return null;

  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  }[position];

  return (
    <span
      className={`relative inline-flex items-center align-middle ${className}`}
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
      onFocus={() => setIsOpen(true)}
      onBlur={() => setIsOpen(false)}
    >
      <button
        type="button"
        aria-label={`Glossary definition for ${entry.title}`}
        className="cursor-help inline-flex items-center justify-center p-0.5 rounded-full hover:bg-slate-100 focus:outline-hidden focus:ring-1 focus:ring-teal-500"
      >
        <HelpCircle className={iconClassName} />
      </button>

      {isOpen && (
        <span
          role="tooltip"
          className={`absolute ${positionClasses} z-50 w-72 p-3 bg-slate-900 text-white text-[11px] leading-relaxed rounded-xl shadow-xl border border-slate-700 pointer-events-none animate-in fade-in zoom-in-95 duration-150 block text-left font-normal normal-case tracking-normal`}
        >
          <strong className="block font-semibold text-teal-300 text-xs mb-1 border-b border-slate-700/80 pb-1">
            {entry.title}
          </strong>
          <span className="text-slate-200">{entry.definition}</span>
        </span>
      )}
    </span>
  );
};
