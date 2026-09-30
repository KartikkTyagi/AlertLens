import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from app.main import app
from app.database import SessionLocal
from app.models import Incident, Alert, AuditLog
from app.schemas import MITRE_TECHNIQUE_NAMES

client = TestClient(app)


def get_analyst_token():
    res = client.post("/auth/login", json={"username": "analyst_demo", "password": "demo1234"})
    return res.json()["access_token"]


def test_data_quality_metrics_match_database():
    """Verify that /metrics matches live database count exactly (no hardcoding)."""
    db = SessionLocal()
    try:
        db_alert_count = db.query(Alert).count()
        db_incident_count = db.query(Incident).count()
        db_actionable_count = db.query(Incident).filter(Incident.confidence_tier == "actionable").count()

        res = client.get("/metrics")
        assert res.status_code == 200
        metrics = res.json()

        assert metrics["total_alerts"] == db_alert_count
        assert metrics["total_incidents"] == db_incident_count
        assert metrics["total_raw_clusters"] == db_incident_count
        assert metrics["actionable_incidents"] == db_actionable_count
        assert metrics["total_alerts"] == 3000
        assert metrics["total_incidents"] == 543
        assert metrics["actionable_incidents"] == 113
    finally:
        db.close()


def test_data_quality_deterministic_sorting_and_pagination():
    """Verify that incident pagination does not duplicate or skip records and is strictly deterministic."""
    token = get_analyst_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch page 1 (limit 20) and page 2 (limit 20, offset 20)
    page1 = client.get("/incidents?tier=actionable&limit=20&offset=0", headers=headers).json()
    page2 = client.get("/incidents?tier=actionable&limit=20&offset=20", headers=headers).json()

    assert len(page1) == 20
    assert len(page2) == 20

    ids_page1 = [inc["incident_id"] for inc in page1]
    ids_page2 = [inc["incident_id"] for inc in page2]

    # No duplicate IDs across pages
    intersection = set(ids_page1).intersection(set(ids_page2))
    assert len(intersection) == 0

    # Strict descending severity score order (or equal if same rank)
    combined = page1 + page2
    for i in range(len(combined) - 1):
        assert combined[i]["severity_score"] >= combined[i + 1]["severity_score"]
        assert combined[i]["severity_rank"] < combined[i + 1]["severity_rank"]


def test_data_quality_tier_filter_consistency():
    """Verify that actionable (113) + informational (430) == all (543) with no overlap."""
    token = get_analyst_token()
    headers = {"Authorization": f"Bearer {token}"}

    actionable = client.get("/incidents?tier=actionable", headers=headers).json()
    informational = client.get("/incidents?tier=informational", headers=headers).json()
    all_incidents = client.get("/incidents?tier=all", headers=headers).json()

    assert len(actionable) == 113
    assert len(informational) == 430
    assert len(all_incidents) == 543
    assert len(actionable) + len(informational) == len(all_incidents)

    actionable_ids = set(inc["incident_id"] for inc in actionable)
    informational_ids = set(inc["incident_id"] for inc in informational)
    all_ids = set(inc["incident_id"] for inc in all_incidents)

    # Disjoint sets
    assert len(actionable_ids.intersection(informational_ids)) == 0
    assert actionable_ids.union(informational_ids) == all_ids


def test_data_quality_null_safety_and_mitre_mapping():
    """Verify that null and missing values in intelligence fields are handled safely."""
    token = get_analyst_token()
    headers = {"Authorization": f"Bearer {token}"}

    incidents = client.get("/incidents?tier=all", headers=headers).json()
    assert len(incidents) == 543

    for inc in incidents:
        # MITRE tag / name consistency
        if inc["mitre_tag"]:
            assert inc["mitre_technique_name"] is not None
            assert inc["mitre_technique_name"] == MITRE_TECHNIQUE_NAMES[inc["mitre_tag"]]
        else:
            assert inc["mitre_tag"] is None
            assert inc["mitre_technique_name"] is None

        # Attack progression valid values
        assert inc["attack_progression"] in (
            "Advanced Kill-Chain Detected",
            "Escalation Chain Detected",
            "None (Isolated Activity)",
        )

        # Correlation confidence bounds and rounding
        assert 0.0 <= inc["correlation_confidence"] <= 1.0
        assert round(inc["correlation_confidence"], 2) == inc["correlation_confidence"]

        # Severity score precision
        assert round(inc["severity_score"], 2) == inc["severity_score"]


def test_data_quality_zero_alerts_handling():
    """Verify single incident detail endpoint handles zero alert incidents safely without error."""
    token = get_analyst_token()
    headers = {"Authorization": f"Bearer {token}"}

    db = SessionLocal()
    try:
        # Create a temporary zero-alert incident
        zero_alert_inc = Incident(
            severity_score=10.0,
            severity_rank=999,
            confidence_tier="informational",
            attack_progression="None (Isolated Activity)",
            correlation_confidence=0.5,
        )
        db.add(zero_alert_inc)
        db.commit()
        db.refresh(zero_alert_inc)
        test_id = zero_alert_inc.incident_id

        # Fetch via API
        res = client.get(f"/incidents/{test_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["alert_count"] == 0
        assert data["incident_id"] == test_id

        # Fetch its alerts
        alerts_res = client.get(f"/incidents/{test_id}/alerts", headers=headers)
        assert alerts_res.status_code == 200
        assert alerts_res.json() == []

        # Cleanup
        db.delete(zero_alert_inc)
        db.commit()
    finally:
        db.close()
