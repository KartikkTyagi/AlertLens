import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models import Alert, Incident


def compute_metrics(db: Optional[Session] = None) -> Dict[str, Any]:
    """Computes real precision, recall, and triage time reduction estimates.
    
    METRIC METHODOLOGY:
    -------------------
    1. Recall: For each planted scenario in ground_truth.json, measures the fraction
       of scenario alerts captured in the dominant incident. Averaged across scenarios.
       (1.0 indicates complete unification into a single incident).
    2. Precision: For the dominant incident of each scenario, measures the fraction of
       its constituent alerts that actually belong to the planted attack vs background noise.
       Averaged across scenarios.
    3. Triage Time Estimate (ILLUSTRATIVE ESTIMATE):
       Assumes ~90 seconds to review an isolated raw alert vs ~180 seconds (3 mins) to review
       an aggregated, correlated incident brief. Reports effective triage time per alert
       and overall percentage reduction in triage labor.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        total_alerts = db.query(Alert).count()
        total_raw_clusters = db.query(Incident).count()
        actionable_incidents = (
            db.query(Incident)
            .filter(Incident.confidence_tier == "actionable")
            .count()
        )
        total_incidents = total_raw_clusters

        gt_path = backend_dir / "data" / "ground_truth.json"
        precision: Optional[float] = None
        recall: Optional[float] = None
        scenario_breakdown: Dict[str, Any] = {}

        if gt_path.exists() and total_incidents > 0:
            with open(gt_path, "r", encoding="utf-8") as f:
                ground_truth = json.load(f)

            scenario_precisions = []
            scenario_recalls = []

            for scenario_name, alert_ids in ground_truth.items():
                if not alert_ids:
                    continue

                scenario_alert_set = set(alert_ids)
                scenario_alerts = db.query(Alert).filter(Alert.alert_id.in_(alert_ids)).all()

                # Count distribution across incidents
                incident_counts: Dict[str, int] = {}
                for a in scenario_alerts:
                    if a.incident_id:
                        incident_counts[a.incident_id] = incident_counts.get(a.incident_id, 0) + 1

                if incident_counts:
                    best_incident_id, best_count = max(
                        incident_counts.items(), key=lambda item: item[1]
                    )
                    scen_recall = best_count / len(scenario_alert_set)

                    total_in_incident = (
                        db.query(Alert)
                        .filter(Alert.incident_id == best_incident_id)
                        .count()
                    )
                    scen_precision = (
                        best_count / total_in_incident if total_in_incident > 0 else 0.0
                    )
                else:
                    scen_recall = 0.0
                    scen_precision = 0.0

                scenario_precisions.append(scen_precision)
                scenario_recalls.append(scen_recall)
                scenario_breakdown[scenario_name] = {
                    "precision": round(scen_precision, 4),
                    "recall": round(scen_recall, 4),
                    "planted_alerts": len(alert_ids),
                }

            if scenario_precisions:
                precision = round(sum(scenario_precisions) / len(scenario_precisions), 4)
                recall = round(sum(scenario_recalls) / len(scenario_recalls), 4)

        # Illustrative Mean-Time-to-Triage (MTTT) labor calculation
        # Raw alert review: ~90s; Actionable incident review: ~180s (informational clusters are background noise)
        time_without_alertlens = total_alerts * 90.0
        time_with_alertlens = actionable_incidents * 180.0
        time_saved_seconds = max(0.0, time_without_alertlens - time_with_alertlens)

        if time_without_alertlens > 0:
            time_saved_pct = round((time_saved_seconds / time_without_alertlens) * 100.0, 1)
            mean_time_per_alert = round(time_with_alertlens / total_alerts, 2)
        else:
            time_saved_pct = 0.0
            mean_time_per_alert = 90.0

        return {
            "total_alerts": total_alerts,
            "total_incidents": total_incidents,
            "total_raw_clusters": total_raw_clusters,
            "actionable_incidents": actionable_incidents,
            "precision": precision,
            "recall": recall,
            "mean_time_to_triage_estimate_seconds": mean_time_per_alert,
            "estimated_time_saved_percentage": time_saved_pct,
            "scenario_breakdown": scenario_breakdown,
        }
    finally:
        if close_session:
            db.close()


def main():
    metrics = compute_metrics()
    print("\n================ EVALUATION METRICS ================")
    print(f"Total Alerts: {metrics['total_alerts']}")
    print(f"Total Incidents: {metrics['total_incidents']}")
    print(f"Overall Precision: {metrics['precision']}")
    print(f"Overall Recall: {metrics['recall']}")
    print(f"Mean Time To Triage (effective s/alert): {metrics['mean_time_to_triage_estimate_seconds']}s (vs 90.0s baseline)")
    print(f"Estimated Triage Labor Reduction: {metrics['estimated_time_saved_percentage']}%")
    print("\nScenario Details:")
    for name, data in metrics.get("scenario_breakdown", {}).items():
        print(f"  [{name}] Precision: {data['precision']} | Recall: {data['recall']}")
    print("====================================================\n")


if __name__ == "__main__":
    main()
