import React from "react";

interface SeverityBadgeProps {
  score?: number;
  rank?: number;
  className?: string;
}

export function getSeverityTier(score?: number, rank?: number): {
  label: "Critical" | "High" | "Medium" | "Low";
  colorClass: string;
  dotClass: string;
} {
  if (score !== undefined) {
    if (score >= 18.0) {
      return {
        label: "Critical",
        colorClass: "bg-rose-50 text-rose-700 border-rose-200",
        dotClass: "bg-rose-500",
      };
    }
    if (score >= 15.0) {
      return {
        label: "High",
        colorClass: "bg-amber-50 text-amber-700 border-amber-200",
        dotClass: "bg-amber-500",
      };
    }
    if (score >= 12.0) {
      return {
        label: "Medium",
        colorClass: "bg-yellow-50 text-yellow-800 border-yellow-200",
        dotClass: "bg-yellow-500",
      };
    }
    return {
      label: "Low",
      colorClass: "bg-emerald-50 text-emerald-700 border-emerald-200",
      dotClass: "bg-emerald-500",
    };
  }

  if (rank !== undefined) {
    if (rank <= 10) {
      return {
        label: "Critical",
        colorClass: "bg-rose-50 text-rose-700 border-rose-200",
        dotClass: "bg-rose-500",
      };
    }
    if (rank <= 50) {
      return {
        label: "High",
        colorClass: "bg-amber-50 text-amber-700 border-amber-200",
        dotClass: "bg-amber-500",
      };
    }
    return {
      label: "Low",
      colorClass: "bg-emerald-50 text-emerald-700 border-emerald-200",
      dotClass: "bg-emerald-500",
    };
  }

  return {
    label: "Low",
    colorClass: "bg-slate-50 text-slate-700 border-slate-200",
    dotClass: "bg-slate-400",
  };
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ score, rank, className = "" }) => {
  const { label, colorClass, dotClass } = getSeverityTier(score, rank);

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClass} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} />
      {label}
      {score !== undefined && <span className="opacity-75 font-mono">({score.toFixed(1)})</span>}
    </span>
  );
};
