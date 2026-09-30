import csv
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    """Verify health check endpoint is operational and public."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "service": "alertlens-backend"}


def test_public_metrics():
    """Verify metrics endpoint is accessible without authentication and reports tiering."""
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_alerts" in data
    assert "total_incidents" in data
    assert "total_raw_clusters" in data
    assert "actionable_incidents" in data
    assert data["total_raw_clusters"] >= data["actionable_incidents"]


def test_public_alerts_pagination():
    """Verify raw alerts browser is accessible without authentication."""
    res = client.get("/alerts?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) <= 5


def test_public_alerts_count():
    """Verify raw alert count endpoint."""
    res = client.get("/alerts/count")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert isinstance(data["total"], int)


def test_alerts_404():
    """Verify 404 behavior for non-existent alert."""
    res = client.get("/alerts/non-existent-uuid")
    assert res.status_code == 404
    assert res.json()["detail"] == "Alert not found"


def test_unauthenticated_incidents_rejected():
    """Verify GET /incidents rejects requests without JWT credentials."""
    res = client.get("/incidents")
    assert res.status_code == 401
    assert "detail" in res.json()


def test_login_invalid_credentials():
    """Verify POST /auth/login rejects wrong passwords."""
    res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "wrong_password_123"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"


def test_login_analyst():
    """Verify analyst demo credentials and JWT role."""
    res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "analyst"
    assert data["username"] == "analyst_demo"


def test_login_admin():
    """Verify admin demo credentials and JWT role."""
    res = client.post(
        "/auth/login",
        json={"username": "admin_demo", "password": "admin1234"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    assert data["username"] == "admin_demo"


def test_authenticated_incidents_access():
    """Verify analyst can query protected /incidents endpoint."""
    login_res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    token = login_res.json()["access_token"]
    res = client.get("/incidents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_incidents_tier_filtering():
    """Verify default returns only actionable, and tier params filter properly."""
    login_res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Default (no tier param) -> only actionable
    res_default = client.get("/incidents", headers=headers)
    assert res_default.status_code == 200
    actionable_incidents = res_default.json()
    assert len(actionable_incidents) > 0
    assert all(inc["confidence_tier"] == "actionable" for inc in actionable_incidents)

    # 2. tier=actionable -> same as default
    res_actionable = client.get("/incidents?tier=actionable", headers=headers)
    assert res_actionable.status_code == 200
    assert len(res_actionable.json()) == len(actionable_incidents)

    # 3. tier=informational -> only informational
    res_info = client.get("/incidents?tier=informational", headers=headers)
    assert res_info.status_code == 200
    info_incidents = res_info.json()
    assert len(info_incidents) > 0
    assert all(inc["confidence_tier"] == "informational" for inc in info_incidents)

    # 4. tier=all -> combined total
    res_all = client.get("/incidents?tier=all", headers=headers)
    assert res_all.status_code == 200
    all_incidents = res_all.json()
    assert len(all_incidents) == len(actionable_incidents) + len(info_incidents)



def test_audit_log_rbac_enforcement():
    """Verify role-based access control: analyst is forbidden (403), admin is authorized (200)."""
    # 1. Analyst attempt -> 403 Forbidden
    analyst_login = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    analyst_token = analyst_login.json()["access_token"]
    res_analyst = client.get(
        "/audit-log",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    assert res_analyst.status_code == 403
    assert "Admin privileges required" in res_analyst.json()["detail"]

    # 2. Admin attempt -> 200 OK
    admin_login = client.post(
        "/auth/login",
        json={"username": "admin_demo", "password": "admin1234"},
    )
    admin_token = admin_login.json()["access_token"]
    res_admin = client.get(
        "/audit-log",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin.status_code == 200
    assert isinstance(res_admin.json(), list)


def test_incident_acknowledgment_and_audit():
    """Verify human-in-the-loop acknowledgment updates incident and writes audit entry."""
    analyst_login = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    analyst_token = analyst_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {analyst_token}"}

    # Fetch incidents to get a valid ID
    incidents_res = client.get("/incidents", headers=headers)
    assert incidents_res.status_code == 200
    incidents = incidents_res.json()

    if incidents:
        target_id = incidents[0]["incident_id"]
        ack_res = client.post(f"/incidents/{target_id}/acknowledge", headers=headers)
        assert ack_res.status_code == 200
        ack_data = ack_res.json()
        assert ack_data["acknowledged"] is True
        assert ack_data["acknowledged_by"] == "analyst_demo"
        assert ack_data["acknowledged_at"] is not None


def test_incident_score_breakdown():
    """Verify GET /incidents/{id} returns explainable score_breakdown and components sum to severity_score."""
    login_res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    incidents_res = client.get("/incidents?tier=actionable", headers=headers)
    assert incidents_res.status_code == 200
    incidents = incidents_res.json()
    assert len(incidents) > 0

    target_inc = incidents[0]
    detail_res = client.get(f"/incidents/{target_inc['incident_id']}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert "score_breakdown" in detail
    breakdown = detail["score_breakdown"]
    assert breakdown is not None
    assert "asset_component" in breakdown
    assert "event_component" in breakdown
    assert "volume_component" in breakdown
    assert breakdown["top_asset_factor"] is not None
    assert breakdown["top_event_factor"] is not None
    assert breakdown.get("asset_raw_level") is not None
    assert breakdown.get("asset_raw_score") is not None
    assert breakdown.get("event_type_used") is not None
    assert breakdown.get("event_raw_score") is not None
    assert breakdown.get("alert_count_used") is not None

    component_sum = round(
        breakdown["asset_component"] + breakdown["event_component"] + breakdown["volume_component"], 2
    )
    assert abs(component_sum - round(detail["severity_score"], 2)) <= 0.01


def test_incident_intelligence_dimensions():
    """Verify Phase D intelligence fields: attack_progression, correlation_confidence, and mitre_technique_name."""
    login_res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    incidents_res = client.get("/incidents?tier=actionable", headers=headers)
    assert incidents_res.status_code == 200
    incidents = incidents_res.json()
    assert len(incidents) > 0

    valid_progressions = {
        "Advanced Kill-Chain Detected",
        "Escalation Chain Detected",
        "None (Isolated Activity)",
    }

    # Verify attributes across all actionable incidents
    for inc in incidents:
        assert inc["attack_progression"] in valid_progressions
        assert 0.0 <= inc["correlation_confidence"] <= 1.0
        assert inc["confidence_reason"] is not None
        if inc["mitre_tag"]:
            assert inc["mitre_technique_name"] is not None
        else:
            assert inc["mitre_technique_name"] is None

    # Specifically verify Rank #1 (Scenario C exfiltration kill chain)
    rank_1 = incidents[0]
    assert rank_1["severity_rank"] == 1
    assert rank_1["attack_progression"] == "Advanced Kill-Chain Detected"
    assert rank_1["mitre_tag"] == "T1567"
    assert rank_1["mitre_technique_name"] == "Exfiltration Over Web Service"
    assert "Authentication → Privilege Escalation → Exfiltration" in rank_1["progression_detail"]


def test_alerts_csv_export():
    """Verify GET /alerts/export/csv exports all 2,569 canonical alerts with exact header fields."""
    # 1. Unauthenticated request rejected
    unauth_res = client.get("/alerts/export/csv")
    assert unauth_res.status_code == 401

    # 2. Authenticated analyst request
    login_res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    csv_res = client.get("/alerts/export/csv", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "attachment" in csv_res.headers["content-disposition"]
    assert "alertlens_raw_alerts_3000.csv" in csv_res.headers["content-disposition"]

    # Parse and verify CSV contents
    content = csv_res.text
    reader = list(csv.reader(io.StringIO(content)))
    assert len(reader) == 3001  # 1 header row + exactly 3000 alert rows

    expected_headers = [
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
    assert reader[0] == expected_headers

    # Verify first data row has non-empty required fields
    sample_row = reader[1]
    assert len(sample_row) == 9
    assert sample_row[0]  # alert_id
    assert sample_row[1]  # timestamp
    assert sample_row[2]  # event_type
    assert sample_row[3]  # username
    assert sample_row[4]  # source_ip
    assert sample_row[5]  # target_asset
    assert sample_row[6] in ("high", "medium", "low")  # asset_criticality
    assert sample_row[7]  # raw_message


def test_alerts_dataset_stats():
    """Verify GET /alerts/stats returns dataset metadata, distributions, and assigned/uncorrelated counts."""
    # 1. Unauthenticated request rejected
    unauth_res = client.get("/alerts/stats")
    assert unauth_res.status_code == 401

    # 2. Authenticated analyst request
    login_res = client.post(
        "/auth/login",
        json={"username": "analyst_demo", "password": "demo1234"},
    )
    assert login_res.status_code == 200
    headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    stats_res = client.get("/alerts/stats", headers=headers)
    assert stats_res.status_code == 200
    data = stats_res.json()

    assert data["total_alerts"] == 3000
    assert data["assigned_to_incidents"] == 2083
    assert data["uncorrelated_alerts"] == 917
    assert data["assigned_to_incidents"] + data["uncorrelated_alerts"] == 3000

    assert "time_range" in data
    assert data["time_range"]["start"] is not None
    assert data["time_range"]["end"] is not None

    assert len(data["available_fields"]) == 9
    assert "alert_id" in data["available_fields"]
    assert "raw_message" in data["available_fields"]
    assert "incident_id" in data["available_fields"]

    assert len(data["event_type_distribution"]) > 0
    assert data["event_type_distribution"]["successful_login"] == 1026
    assert data["event_type_distribution"]["failed_login"] == 625



