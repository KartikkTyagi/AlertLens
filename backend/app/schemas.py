from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    timestamp: datetime
    source_ip: str
    username: str
    event_type: str
    target_asset: str
    asset_criticality: str
    raw_message: str
    incident_id: Optional[str] = None


class TimeRangeOut(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class AlertDatasetStatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_alerts: int
    available_fields: List[str]
    time_range: TimeRangeOut
    event_type_distribution: dict
    criticality_distribution: dict
    assigned_to_incidents: int
    uncorrelated_alerts: int


class ScoreBreakdownOut(BaseModel):
    asset_component: float = 0.0
    event_component: float = 0.0
    volume_component: float = 0.0
    top_asset_factor: Optional[str] = None
    top_event_factor: Optional[str] = None
    asset_raw_level: Optional[str] = None
    asset_raw_score: Optional[int] = 1
    event_type_used: Optional[str] = None
    event_raw_score: Optional[int] = 1
    alert_count_used: Optional[int] = 0


MITRE_TECHNIQUE_NAMES = {
    "T1567": "Exfiltration Over Web Service",
    "T1068": "Exploitation for Privilege Escalation",
    "T1110": "Brute Force",
    "T1110.001": "Password Guessing",
    "T1078": "Valid Accounts",
    "T1021": "Remote Services",
    "T1005": "Data from Local System",
    "T1098": "Account Manipulation",
}


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    severity_score: float
    severity_rank: int
    mitre_tag: Optional[str] = None
    mitre_technique_name: Optional[str] = None
    alert_count: int = 0
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    confidence_tier: str = "actionable"
    attack_progression: str = "None (Isolated Activity)"
    progression_detail: Optional[str] = None
    correlation_confidence: float = 0.75
    confidence_reason: Optional[str] = None
    score_breakdown: Optional[ScoreBreakdownOut] = None


class IncidentBriefOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    summary_text: str
    source_alert_ids: List[str]
    mitre_tag: Optional[str] = None
    mitre_technique_name: Optional[str] = None


class MetricsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_alerts: int
    total_incidents: int
    total_raw_clusters: int
    actionable_incidents: int
    precision: Optional[float] = None
    recall: Optional[float] = None
    mean_time_to_triage_estimate_seconds: Optional[float] = None
    estimated_time_saved_percentage: Optional[float] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, description="Username of analyst or administrator")
    password: str = Field(..., min_length=1, max_length=128, description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    username: str
    role: str


class AcknowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    incident_id: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    action: str
    incident_id: Optional[str] = None
    timestamp: datetime
    user_id: Optional[str] = None
