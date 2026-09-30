import React from "react";
import { ShieldAlert } from "lucide-react";

interface MitreBadgeProps {
  tag?: string | null;
  code?: string | null;
  techniqueName?: string | null;
  className?: string;
  showIcon?: boolean;
  showFullName?: boolean;
}

export const MITRE_TECHNIQUE_NAMES: Record<string, string> = {
  T1567: "Exfiltration Over Web Service",
  T1005: "Data from Local System",
  "T1110.001": "Password Guessing",
  T1110: "Brute Force",
  T1078: "Valid Accounts",
  T1068: "Exploitation for Privilege Escalation",
};

export const MitreBadge: React.FC<MitreBadgeProps> = ({
  tag,
  code,
  techniqueName,
  className = "",
  showIcon = true,
  showFullName = false,
}) => {
  const effectiveTag = tag || code;
  if (!effectiveTag || effectiveTag === "-" || effectiveTag === "—" || effectiveTag === "None" || effectiveTag === "null") {
    return (
      <span
        title="No MITRE ATT&CK technique pattern identified in current telemetry"
        className={`inline-flex items-center text-xs text-slate-400 font-sans cursor-help ${className}`}
      >
        Not mapped
      </span>
    );
  }

  const name = techniqueName || MITRE_TECHNIQUE_NAMES[effectiveTag] || "";

  return (
    <span
      title={name ? `${effectiveTag}: ${name}` : effectiveTag}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-indigo-200 bg-indigo-50/80 text-indigo-700 text-xs font-mono font-medium tracking-wide ${className}`}
    >
      {showIcon && <ShieldAlert className="w-3.5 h-3.5 text-indigo-500 shrink-0" />}
      <span>{effectiveTag}</span>
      {showFullName && name && (
        <span className="font-sans text-indigo-800 font-normal">
          &middot; {name}
        </span>
      )}
    </span>
  );
};

