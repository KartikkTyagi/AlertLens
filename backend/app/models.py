import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from .database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="analyst")  # analyst, admin


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    source_ip = Column(String, nullable=False)
    username = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    target_asset = Column(String, nullable=False)
    asset_criticality = Column(String, nullable=False)
    raw_message = Column(Text, nullable=False)
    incident_id = Column(String, ForeignKey("incidents.incident_id"), nullable=True, index=True)

    incident = relationship("Incident", back_populates="alerts")


class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String, primary_key=True, default=generate_uuid)
    severity_score = Column(Float, nullable=False, default=0.0)
    severity_rank = Column(Integer, nullable=False, default=0, index=True)
    mitre_tag = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Phase 9: Human-in-the-loop acknowledgment
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    # Triage tiering: actionable vs informational
    confidence_tier = Column(String, nullable=False, default="actionable", index=True)

    # Production-grade intelligence dimensions
    attack_progression = Column(String, nullable=False, default="None (Isolated Activity)")
    progression_detail = Column(String, nullable=True)
    correlation_confidence = Column(Float, nullable=False, default=0.75)
    confidence_reason = Column(String, nullable=True)

    # Transparent score breakdown components
    score_asset_component = Column(Float, nullable=False, default=0.0)
    score_event_component = Column(Float, nullable=False, default=0.0)
    score_volume_component = Column(Float, nullable=False, default=0.0)
    top_asset_factor = Column(String, nullable=True)
    top_event_factor = Column(String, nullable=True)
    asset_raw_level = Column(String, nullable=True)
    asset_raw_score = Column(Integer, nullable=False, default=1)
    event_type_used = Column(String, nullable=True)
    event_raw_score = Column(Integer, nullable=False, default=1)
    alert_count_used = Column(Integer, nullable=False, default=0)

    alerts = relationship("Alert", back_populates="incident")
    brief = relationship("IncidentBrief", back_populates="incident", uselist=False)


class IncidentBrief(Base):
    __tablename__ = "incident_briefs"

    brief_id = Column(String, primary_key=True, default=generate_uuid)
    incident_id = Column(String, ForeignKey("incidents.incident_id"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    source_alert_ids = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    incident = relationship("Incident", back_populates="brief")


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(String, primary_key=True, default=generate_uuid)
    action = Column(String, nullable=False)
    incident_id = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = Column(String, nullable=True)
