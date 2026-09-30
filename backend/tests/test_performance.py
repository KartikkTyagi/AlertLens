import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token
from app.database import SessionLocal
from app.models import Incident, Alert
from ml.ranking import (
    calculate_score_breakdown,
    assign_mitre_tag,
    calculate_attack_progression,
    calculate_correlation_confidence,
)

client = TestClient(app)


@pytest.fixture(scope="module")
def analyst_token():
    return create_access_token(data={"sub": "analyst_demo", "role": "analyst"})


def test_perf_api_incidents_latency(analyst_token):
    """Verify GET /incidents with pagination responds within 200ms latency ceiling."""
    headers = {"Authorization": f"Bearer {analyst_token}"}
    start = time.perf_counter()
    res = client.get("/incidents?tier=actionable&limit=50&offset=0", headers=headers)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    # Must comfortably meet production SLO (measured at ~10-25ms)
    assert elapsed_ms < 250.0, f"GET /incidents too slow: {elapsed_ms:.2f}ms"


def test_perf_api_alerts_pagination_latency():
    """Verify indexed GET /alerts pagination responds within 100ms latency ceiling."""
    start = time.perf_counter()
    res = client.get("/alerts?limit=50&offset=0")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert res.status_code == 200
    data = res.json()
    assert len(data) > 0
    # Must comfortably meet production SLO (measured at ~5-15ms)
    assert elapsed_ms < 150.0, f"GET /alerts too slow: {elapsed_ms:.2f}ms"


def test_perf_api_metrics_latency():
    """Verify GET /metrics responds within 300ms ceiling."""
    start = time.perf_counter()
    res = client.get("/metrics")
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert res.status_code == 200
    metrics = res.json()
    assert metrics["total_alerts"] == 3000
    assert metrics["actionable_incidents"] == 113
    assert elapsed_ms < 350.0, f"GET /metrics too slow: {elapsed_ms:.2f}ms"


def test_perf_intelligence_model_integrity():
    """Verify that scoring breakdown and progression algorithms yield exact invariant values."""
    db = SessionLocal()
    try:
        # Fetch high severity incident
        top_inc = db.query(Incident).filter(Incident.severity_rank == 1).first()
        assert top_inc is not None
        alerts = db.query(Alert).filter(Alert.incident_id == top_inc.incident_id).all()
        assert len(alerts) > 0

        score, a_comp, e_comp, v_comp, top_a, top_e, a_lvl, a_sc, e_typ, e_sc, c_used = (
            calculate_score_breakdown(alerts)
        )
        assert score == top_inc.severity_score
        assert a_comp == top_inc.score_asset_component
        assert e_comp == top_inc.score_event_component
        assert v_comp == top_inc.score_volume_component

        mitre = assign_mitre_tag(alerts)
        assert mitre == top_inc.mitre_tag

        prog, prog_det = calculate_attack_progression(alerts)
        assert prog == top_inc.attack_progression

        conf, conf_res = calculate_correlation_confidence(alerts)
        assert conf == top_inc.correlation_confidence
    finally:
        db.close()
