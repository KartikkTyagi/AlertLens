from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import MetricsOut
from ml.metrics import compute_metrics

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("", response_model=MetricsOut)
def get_metrics(db: Session = Depends(get_db)):
    """Retrieve operational and evaluation metrics against ground truth.
    
    Returns total alerts, total incidents, precision, recall, and
    estimated mean-time-to-triage reduction.
    """
    metrics_data = compute_metrics(db)
    return MetricsOut(
        total_alerts=metrics_data["total_alerts"],
        total_incidents=metrics_data["total_incidents"],
        total_raw_clusters=metrics_data["total_raw_clusters"],
        actionable_incidents=metrics_data["actionable_incidents"],
        precision=metrics_data["precision"],
        recall=metrics_data["recall"],
        mean_time_to_triage_estimate_seconds=metrics_data["mean_time_to_triage_estimate_seconds"],
        estimated_time_saved_percentage=metrics_data["estimated_time_saved_percentage"],
    )

