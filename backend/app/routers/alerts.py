import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Alert, User
from ..schemas import AlertOut, AlertDatasetStatsOut, TimeRangeOut
from ..auth import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=List[AlertOut])
def get_alerts(
    limit: int = Query(50, ge=1, le=500, description="Max number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    event_type: Optional[str] = Query(None, max_length=64, description="Filter by event type"),
    asset_criticality: Optional[str] = Query(None, max_length=32, description="Filter by asset criticality"),
    username: Optional[str] = Query(None, max_length=64, description="Filter by username"),
    source_ip: Optional[str] = Query(None, max_length=64, description="Filter by source IP"),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of alerts ordered by timestamp descending."""
    query = db.query(Alert)

    if event_type:
        query = query.filter(Alert.event_type == event_type)
    if asset_criticality:
        query = query.filter(Alert.asset_criticality == asset_criticality)
    if username:
        query = query.filter(Alert.username == username)
    if source_ip:
        query = query.filter(Alert.source_ip == source_ip)

    alerts = query.order_by(Alert.timestamp.desc(), Alert.alert_id.asc()).offset(offset).limit(limit).all()
    return alerts


@router.get("/count")
def get_alerts_count(db: Session = Depends(get_db)):
    """Retrieve the total count of alerts currently stored."""
    total = db.query(Alert).count()
    return {"total": total}


@router.get("/stats", response_model=AlertDatasetStatsOut)
def get_alerts_dataset_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve comprehensive dataset metrics for the complete canonical alert stream."""
    total = db.query(Alert).count()
    assigned = db.query(Alert).filter(Alert.incident_id.isnot(None)).count()
    uncorrelated = total - assigned

    time_bounds = db.query(
        func.min(Alert.timestamp).label("min_ts"),
        func.max(Alert.timestamp).label("max_ts"),
    ).first()

    event_dist_rows = (
        db.query(Alert.event_type, func.count(Alert.alert_id))
        .group_by(Alert.event_type)
        .order_by(func.count(Alert.alert_id).desc())
        .all()
    )
    event_type_distribution = {row[0]: row[1] for row in event_dist_rows}

    crit_dist_rows = (
        db.query(Alert.asset_criticality, func.count(Alert.alert_id))
        .group_by(Alert.asset_criticality)
        .order_by(func.count(Alert.alert_id).desc())
        .all()
    )
    criticality_distribution = {row[0]: row[1] for row in crit_dist_rows}

    fields = [
        "alert_id",
        "timestamp",
        "event_type",
        "username",
        "source_ip",
        "target_asset",
        "asset_criticality",
        "raw_message",
        "incident_id",
    ]

    return AlertDatasetStatsOut(
        total_alerts=total,
        available_fields=fields,
        time_range=TimeRangeOut(
            start=time_bounds.min_ts if time_bounds else None,
            end=time_bounds.max_ts if time_bounds else None,
        ),
        event_type_distribution=event_type_distribution,
        criticality_distribution=criticality_distribution,
        assigned_to_incidents=assigned,
        uncorrelated_alerts=uncorrelated,
    )


@router.get("/export/csv")
def export_alerts_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export complete canonical raw alert dataset as RFC 4180 CSV."""
    alerts = db.query(Alert).order_by(Alert.timestamp.desc(), Alert.alert_id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    headers = [
        "alert_id",
        "timestamp",
        "event_type",
        "username",
        "source_ip",
        "target_asset",
        "asset_criticality",
        "raw_message",
        "incident_id",
    ]
    writer.writerow(headers)

    for a in alerts:
        writer.writerow([
            a.alert_id,
            a.timestamp.isoformat() if a.timestamp else "",
            a.event_type,
            a.username,
            a.source_ip,
            a.target_asset,
            a.asset_criticality,
            a.raw_message,
            a.incident_id or "",
        ])

    csv_content = output.getvalue()
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=alertlens_raw_alerts_{len(alerts)}.csv",
            "X-Total-Count": str(len(alerts)),
        },
    )


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert_by_id(
    alert_id: str = Path(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$", description="Alert unique identifier"),
    db: Session = Depends(get_db),
):
    """Retrieve a single alert by its UUID."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
