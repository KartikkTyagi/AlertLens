"""
AlertLens — Phase 7 End-to-End Product QA & Analyst Journey Audit
Automates the full 15-step analyst and admin verification lifecycle.
"""

import sys
import time
from pathlib import Path
import httpx

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8000"

def run_qa_audit():
    print("=" * 80)
    print("ALERTLENS PHASE 7 — PRODUCT UX & END-TO-END QA AUDIT")
    print("=" * 80)

    with httpx.Client(timeout=10.0) as client:
        # 1. Analyst Login
        print("\n[Step 1] Testing Analyst Login (analyst_demo)...")
        login_res = client.post(f"{BASE_URL}/auth/login", json={"username": "analyst_demo", "password": "demo1234"})
        assert login_res.status_code == 200, f"Analyst login failed: {login_res.text}"
        analyst_token = login_res.json()["access_token"]
        analyst_headers = {"Authorization": f"Bearer {analyst_token}"}
        print(" -> Success: JWT issued for role 'analyst'.")

        # 2. Dashboard Metrics
        print("\n[Step 2] Fetching Public / Dashboard Metrics...")
        metrics_res = client.get(f"{BASE_URL}/metrics")
        assert metrics_res.status_code == 200
        metrics = metrics_res.json()
        print(f" -> Metrics: {metrics['total_alerts']} alerts | {metrics['total_incidents']} clusters | {metrics['actionable_incidents']} actionable")
        print(f" -> Efficacy: {metrics['recall']*100:.1f}% recall | {metrics['precision']*100:.1f}% precision | {metrics['estimated_time_saved_percentage']}% MTTT saved")

        # 3. Retrieve Incidents List
        print("\n[Step 3] Fetching Prioritized Incidents (Actionable Tier)...")
        incidents_res = client.get(f"{BASE_URL}/incidents?tier=actionable&limit=20", headers=analyst_headers)
        assert incidents_res.status_code == 200
        incidents = incidents_res.json()
        assert len(incidents) > 0
        top_incident = incidents[0]
        print(f" -> Found {len(incidents)} actionable incidents. Top incident: #{top_incident['severity_rank']} (Score: {top_incident['severity_score']}) ID: {top_incident['incident_id']}")

        # 4. Deep Inspection of Top Incident (The 5 Dimensions)
        print("\n[Step 4] Inspecting Top Incident 5 Dimensions...")
        inc_id = top_incident["incident_id"]
        detail_res = client.get(f"{BASE_URL}/incidents/{inc_id}", headers=analyst_headers)
        assert detail_res.status_code == 200
        inc_data = detail_res.json()

        print(f" -> Dim 1 (Severity Score): {inc_data['severity_score']} (Rank #{inc_data['severity_rank']})")
        print(f"    Breakdown: Asset=+{inc_data['score_breakdown']['asset_component']} | Event=+{inc_data['score_breakdown']['event_component']} | Volume=+{inc_data['score_breakdown']['volume_component']}")
        print(f" -> Dim 2 (Attack Progression): {inc_data['attack_progression']} ({inc_data['progression_detail'] or 'Single stage'})")
        print(f" -> Dim 3 (Correlation Confidence): {int(inc_data['correlation_confidence']*100)}% ({inc_data['confidence_reason']})")
        print(f" -> Dim 4 (MITRE ATT&CK): {inc_data['mitre_tag']} ({inc_data['mitre_technique_name']})")

        # 5. Fetch and Inspect AI Incident Brief
        print("\n[Step 5] Fetching AI Incident Brief & Logging View...")
        brief_res = client.get(f"{BASE_URL}/incidents/{inc_id}/brief", headers=analyst_headers)
        assert brief_res.status_code == 200
        brief_data = brief_res.json()
        has_summary = len(brief_data.get("summary_text", "")) > 20
        print(f" -> Dim 5 (AI Brief): {'Present & Structured' if has_summary else 'Fallback Mode'}")
        print(f" -> Traceable Alert References: {len(brief_data.get('source_alert_ids', []))} alerts cited")

        # 6. Fetch Underlying Correlated Alerts
        print("\n[Step 6] Fetching Underlying Evidence (Child Alerts)...")
        alerts_res = client.get(f"{BASE_URL}/incidents/{inc_id}/alerts", headers=analyst_headers)
        assert alerts_res.status_code == 200
        alerts = alerts_res.json()
        print(f" -> Retrieved {len(alerts)} raw alerts for incident {inc_id[:8]}...")
        assert len(alerts) == top_incident["alert_count"]

        # 7. Analyst Acknowledgment Workflow
        print("\n[Step 7] Testing Incident Acknowledgment...")
        ack_res = client.post(f"{BASE_URL}/incidents/{inc_id}/acknowledge", headers=analyst_headers)
        assert ack_res.status_code == 200
        ack_data = ack_res.json()
        assert ack_data["acknowledged"] is True
        assert ack_data["acknowledged_by"] == "analyst_demo"
        print(f" -> Success: Incident {inc_id[:8]} acknowledged by {ack_data['acknowledged_by']}.")

        # 8. Access Control: Analyst Blocked from Admin Audit Log
        print("\n[Step 8] Verifying RBAC: Analyst Forbidden from /audit-log...")
        audit_analyst_res = client.get(f"{BASE_URL}/audit-log", headers=analyst_headers)
        assert audit_analyst_res.status_code == 403, f"Expected 403, got {audit_analyst_res.status_code}"
        print(" -> Success: 403 Forbidden properly returned for non-admin.")

        # 9. Admin Login & Audit Trail Verification
        print("\n[Step 9] Testing Admin Login & Audit Trail Inspection...")
        admin_login_res = client.post(f"{BASE_URL}/auth/login", json={"username": "admin_demo", "password": "admin1234"})
        assert admin_login_res.status_code == 200
        admin_token = admin_login_res.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        audit_res = client.get(f"{BASE_URL}/audit-log?limit=10", headers=admin_headers)
        assert audit_res.status_code == 200
        audit_logs = audit_res.json()
        assert len(audit_logs) > 0
        actions = [log["action"] for log in audit_logs]
        print(f" -> Success: Admin retrieved {len(audit_logs)} audit records.")
        print(f" -> Recent audit actions: {actions[:4]}")
        assert "acknowledged_incident" in actions

        # 10. Failure-Mode QA
        print("\n[Step 10] Testing Failure-Mode Scenarios...")
        # A: Invalid credentials
        bad_login = client.post(f"{BASE_URL}/auth/login", json={"username": "fake", "password": "wrong"})
        assert bad_login.status_code == 401
        print(" -> Failure Mode A (Bad Login): 401 Unauthorized verified.")

        # B: Non-existent incident
        bad_inc = client.get(f"{BASE_URL}/incidents/nonexistent-uuid-9999", headers=analyst_headers)
        assert bad_inc.status_code == 404
        print(" -> Failure Mode B (Missing Incident): 404 Not Found verified.")

        # C: Malformed query parameter
        bad_param = client.get(f"{BASE_URL}/incidents?tier=INVALID_TIER", headers=analyst_headers)
        assert bad_param.status_code == 422
        print(" -> Failure Mode C (Invalid Tier): 422 Unprocessable Entity verified.")

        # D: Expired/Tampered Token
        bad_token_res = client.get(f"{BASE_URL}/incidents", headers={"Authorization": "Bearer fake.tampered.token"})
        assert bad_token_res.status_code == 401
        print(" -> Failure Mode D (Tampered Token): 401 Unauthorized verified.")

    print("\n" + "=" * 80)
    print("ALL 10 END-TO-END QA STEPS PASSED SUCCESSFULLY (100% OPERATIONAL)")
    print("=" * 80)

if __name__ == "__main__":
    run_qa_audit()
