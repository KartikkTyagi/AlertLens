export interface Alert {
  alert_id: string;
  timestamp: string;
  source_ip: string;
  username: string;
  event_type: string;
  target_asset: string;
  asset_criticality: "low" | "medium" | "high" | string;
  raw_message: string;
  incident_id: string | null;
}

export interface ScoreBreakdown {
  asset_component: number;
  event_component: number;
  volume_component: number;
  top_asset_factor: string | null;
  top_event_factor: string | null;
  asset_raw_level?: string | null;
  asset_raw_score?: number | null;
  event_type_used?: string | null;
  event_raw_score?: number | null;
  alert_count_used?: number | null;
}

export interface Incident {
  incident_id: string;
  severity_score: number;
  severity_rank: number;
  mitre_tag: string | null;
  mitre_technique_name?: string | null;
  alert_count: number;
  created_at: string;
  acknowledged?: boolean;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  confidence_tier?: "actionable" | "informational" | string;
  attack_progression?: string;
  progression_detail?: string | null;
  correlation_confidence?: number;
  confidence_reason?: string | null;
  score_breakdown?: ScoreBreakdown | null;
}

export interface IncidentBrief {
  incident_id: string;
  summary_text: string;
  source_alert_ids: string[];
  mitre_tag: string | null;
  mitre_technique_name?: string | null;
}

export interface Metrics {
  total_alerts: number;
  total_incidents: number;
  total_raw_clusters?: number;
  actionable_incidents?: number;
  precision: number | null;
  recall: number | null;
  mean_time_to_triage_estimate_seconds: number | null;
  estimated_time_saved_percentage: number | null;
}

export interface User {
  username: string;
  role: "analyst" | "admin" | string;
}

export interface AuthSession {
  access_token: string;
  token_type: string;
  role: string;
  username: string;
}

export interface AuditLogEntry {
  log_id: string;
  action: string;
  incident_id: string | null;
  timestamp: string;
  user_id: string | null;
}

export interface AlertDatasetStats {
  total_alerts: number;
  available_fields: string[];
  time_range: {
    start: string | null;
    end: string | null;
  };
  event_type_distribution: Record<string, number>;
  criticality_distribution: Record<string, number>;
  assigned_to_incidents: number;
  uncorrelated_alerts: number;
}
