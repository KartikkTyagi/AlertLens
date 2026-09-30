import React from "react";
import { GlossaryTooltip, GlossaryTerm } from "./GlossaryTooltip";

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: React.ReactNode;
  trend?: {
    positive?: boolean;
    text: string;
  };
  className?: string;
  glossaryTerm?: GlossaryTerm;
  accent?: "teal" | "amber" | "rose" | "graphite";
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon,
  trend,
  className = "",
  glossaryTerm,
  accent = "graphite",
}) => {
  const accentBorder =
    accent === "teal"
      ? "hover:border-teal-300/80"
      : accent === "amber"
      ? "hover:border-amber-300/80"
      : accent === "rose"
      ? "hover:border-rose-300/80"
      : "hover:border-ivory-400";

  return (
    <div
      className={`relative rounded-2xl border border-ivory-300/80 bg-white/85 backdrop-blur-md p-5 shadow-crystal hover:shadow-crystal-hover transition-all duration-200 flex flex-col justify-between ${accentBorder} ${className}`}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-graphite-500 inline-flex items-center gap-1.5 font-mono">
          {label}
          {glossaryTerm && <GlossaryTooltip term={glossaryTerm} position="bottom" />}
        </span>
        {icon && (
          <div className="p-2 rounded-xl bg-ivory-50 text-graphite-700 border border-ivory-200 shadow-2xs">
            {icon}
          </div>
        )}
      </div>

      <div className="mt-3">
        <div className="text-2xl sm:text-3xl font-black tracking-tight text-graphite-950 font-mono">
          {value}
        </div>
        {(subtext || trend) && (
          <div className="mt-1 flex items-center gap-2 text-xs text-graphite-500">
            {trend && (
              <span
                className={`font-semibold ${
                  trend.positive ? "text-emerald-700" : "text-amber-700"
                }`}
              >
                {trend.text}
              </span>
            )}
            {subtext && <span className="truncate">{subtext}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
