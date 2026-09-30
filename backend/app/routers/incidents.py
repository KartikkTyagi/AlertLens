from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, Incident, IncidentBrief, AuditLog, User
from ..schemas import AlertOut, IncidentBriefOut, IncidentOut, ScoreBreakdownOut, MITRE_TECHNIQUE_NAMES
from ..auth import get_current_user

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def make_score_breakdown(inc: Incident) -> ScoreBreakdownOut:
    return ScoreBreakdownOut(
        asset_component=round(getattr(inc, "score_asset_component", 0.0) or 0.0, 2),
        event_component=round(getattr(inc, "score_event_component", 0.0) or 0.0, 2),
        volume_component=round(getattr(inc, "score_volume_component", 0.0) or 0.0, 2),
        top_asset_factor=getattr(inc, "top_asset_factor", None),
        top_event_factor=getattr(inc, "top_event_factor", None),
        asset_raw_level=getattr(inc, "asset_raw_level", None),
        asset_raw_score=getattr(inc, "asset_raw_score", 1),
        event_type_used=getattr(inc, "event_type_used", None),
        event_raw_score=getattr(inc, "event_raw_score", 1),
        alert_count_used=getattr(inc, "alert_count_used", 0),
    )


def make_incident_out(inc: Incident, alert_count: int) -> IncidentOut:
    mitre_name = MITRE_TECHNIQUE_NAMES.get(inc.mitre_tag) if inc.mitre_tag else None
    return IncidentOut(
        incident_id=inc.incident_id,
        severity_score=round(inc.severity_score, 2),
        severity_rank=inc.severity_rank,
        mitre_tag=inc.mitre_tag,
        mitre_technique_name=mitre_name,
        alert_count=alert_count,
        created_at=inc.created_at,
        acknowledged=inc.acknowledged,
        acknowledged_by=inc.acknowledged_by,
        acknowledged_at=inc.acknowledged_at,
        confidence_tier=getattr(inc, "confidence_tier", "actionable") or "actionable",
        attack_progression=getattr(inc, "attack_progression", "None (Isolated Activity)") or "None (Isolated Activity)",
        progression_detail=getattr(inc, "progression_detail", None),
        correlation_confidence=round(getattr(inc, "correlation_confidence", 0.75) or 0.75, 2),
        confidence_reason=getattr(inc, "confidence_reason", None),
        score_breakdown=make_score_breakdown(inc),
    )


@router.get("", response_model=List[IncidentOut])
def get_incidents(
    tier: Optional[str] = Query("actionable", pattern=r"^(actionable|informational|all)$", description="Tier filter: actionable | informational | all"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Max incidents to return"),
    offset: Optional[int] = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve incidents ordered by severity rank ascending. Requires authentication.
    
    Query params:
    - tier: 'actionable' (default) | 'informational' | 'all'
    - limit: optional max items (up to 1000)
    - offset: optional pagination offset
    """
    query = (
        db.query(Incident, func.count(Alert.alert_id).label("alert_count"))
        .outerjoin(Alert, Incident.incident_id == Alert.incident_id)
        .group_by(Incident.incident_id)
    )

    if tier and tier.lower() in ("actionable", "informational"):
        query = query.filter(Incident.confidence_tier == tier.lower())
    elif tier and tier.lower() == "all":
        pass  # return all incidents

    query = query.order_by(Incident.severity_rank.asc(), Incident.incident_id.asc())
    if offset:
        query = query.offset(offset)
    if limit is not None:
        query = query.limit(limit)

    results = query.all()

    incidents_out = []
    for inc, alert_count in results:
        incidents_out.append(make_incident_out(inc, alert_count))
    return incidents_out


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident_by_id(
    incident_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Incident unique identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a single incident by ID with computed alert count. Requires authentication."""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    alert_count = db.query(Alert).filter(Alert.incident_id == incident_id).count()
    return make_incident_out(inc, alert_count)


@router.get("/{incident_id}/alerts", response_model=List[AlertOut])
def get_incident_alerts(
    incident_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Incident unique identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all raw alerts associated with an incident. Requires authentication."""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    alerts = (
        db.query(Alert)
        .filter(Alert.incident_id == incident_id)
        .order_by(Alert.timestamp.asc(), Alert.alert_id.asc())
        .all()
    )
    return alerts


@router.get("/{incident_id}/brief", response_model=IncidentBriefOut)
def get_incident_brief(
    incident_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Incident unique identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the AI incident brief and log the view in the audit trail. Requires authentication."""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    brief = db.query(IncidentBrief).filter(IncidentBrief.incident_id == incident_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="No brief generated yet for this incident")

    # Enterprise Audit Trail: log viewing of AI brief
    audit_entry = AuditLog(
        action="viewed_brief",
        incident_id=incident_id,
        user_id=current_user.username,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit_entry)
    db.commit()

    mitre_name = MITRE_TECHNIQUE_NAMES.get(inc.mitre_tag) if inc.mitre_tag else None
    return IncidentBriefOut(
        incident_id=brief.incident_id,
        summary_text=brief.summary_text,
        source_alert_ids=brief.source_alert_ids,
        mitre_tag=inc.mitre_tag,
        mitre_technique_name=mitre_name,
    )


@router.post("/{incident_id}/brief/generate", response_model=IncidentBriefOut)
def generate_incident_brief_endpoint(
    incident_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Incident unique identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates or regenerates an AI incident brief on-demand using Groq LLM."""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    alerts = db.query(Alert).filter(Alert.incident_id == incident_id).order_by(Alert.timestamp.asc()).all()
    if not alerts:
        raise HTTPException(status_code=400, detail="Cannot generate brief: no source alerts linked to this incident")

    import uuid
    from ml.summarize import generate_summary
    summary_text, source_ids = generate_summary(inc, alerts)

    brief = db.query(IncidentBrief).filter(IncidentBrief.incident_id == incident_id).first()
    now = datetime.now(timezone.utc)
    if not brief:
        brief = IncidentBrief(
            brief_id=str(uuid.uuid4()),
            incident_id=incident_id,
            summary_text=summary_text,
            source_alert_ids=source_ids,
            created_at=now,
        )
        db.add(brief)
    else:
        brief.summary_text = summary_text
        brief.source_alert_ids = source_ids
        brief.created_at = now
    db.commit()
    db.refresh(brief)

    # Log generation in audit trail
    audit_entry = AuditLog(
        action="generated_brief",
        incident_id=incident_id,
        user_id=current_user.username,
        timestamp=now,
    )
    db.add(audit_entry)
    db.commit()

    mitre_name = MITRE_TECHNIQUE_NAMES.get(inc.mitre_tag) if inc.mitre_tag else None
    return IncidentBriefOut(
        incident_id=brief.incident_id,
        summary_text=brief.summary_text,
        source_alert_ids=brief.source_alert_ids,
        mitre_tag=inc.mitre_tag,
        mitre_technique_name=mitre_name,
    )


@router.post("/{incident_id}/acknowledge", response_model=IncidentOut)
def acknowledge_incident(
    incident_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Incident unique identifier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Human-in-the-loop: mark an incident as acknowledged by the current analyst and record audit log."""
    inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now = datetime.now(timezone.utc)
    inc.acknowledged = True
    inc.acknowledged_by = current_user.username
    inc.acknowledged_at = now

    audit_entry = AuditLog(
        action="acknowledged_incident",
        incident_id=incident_id,
        user_id=current_user.username,
        timestamp=now,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(inc)

    alert_count = db.query(Alert).filter(Alert.incident_id == incident_id).count()
    return make_incident_out(inc, alert_count)
