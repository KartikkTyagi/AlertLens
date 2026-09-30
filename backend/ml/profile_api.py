"""
AlertLens — API Performance Profiler
Measures real response times, payload sizes, and database execution behavior
across canonical endpoints under realistic data volume.
"""

import time
import httpx
import json

BASE_URL = "http://localhost:8000"

def get_auth_token(client: httpx.Client):
    res = client.post(f"{BASE_URL}/auth/login", json={"username": "analyst_demo", "password": "demo1234"})
    res.raise_for_status()
    return res.json()["access_token"]

def profile_endpoint(client: httpx.Client, name, method, url, headers=None, params=None, json_body=None, repeat=5):
    durations = []
    payload_size = 0
    status_code = None

    for _ in range(repeat):
        start = time.perf_counter()
        if method == "GET":
            res = client.get(url, headers=headers, params=params)
        elif method == "POST":
            res = client.post(url, headers=headers, json=json_body)
        duration = (time.perf_counter() - start) * 1000.0
        durations.append(duration)
        payload_size = len(res.content)
        status_code = res.status_code

    avg_ms = sum(durations) / len(durations)
    min_ms = min(durations)
    max_ms = max(durations)
    return {
        "endpoint": name,
        "method": method,
        "status": status_code,
        "avg_ms": round(avg_ms, 2),
        "min_ms": round(min_ms, 2),
        "max_ms": round(max_ms, 2),
        "payload_bytes": payload_size,
    }

def main():
    with httpx.Client(timeout=10.0) as client:
        token = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Fetch a sample incident ID for detail calls
        incidents_res = client.get(f"{BASE_URL}/incidents?tier=actionable&limit=5", headers=headers)
        sample_incident_id = incidents_res.json()[0]["incident_id"]

        # Fetch a sample alert ID
        alerts_res = client.get(f"{BASE_URL}/alerts?limit=5")
        sample_alert_id = alerts_res.json()[0]["alert_id"]

        tests = [
            # Incidents
            ("GET /incidents (actionable, first 50)", "GET", f"{BASE_URL}/incidents", headers, {"tier": "actionable", "limit": 50, "offset": 0}),
            ("GET /incidents (actionable, offset 50)", "GET", f"{BASE_URL}/incidents", headers, {"tier": "actionable", "limit": 50, "offset": 50}),
            ("GET /incidents (informational, first 50)", "GET", f"{BASE_URL}/incidents", headers, {"tier": "informational", "limit": 50, "offset": 0}),
            ("GET /incidents (informational, offset 200)", "GET", f"{BASE_URL}/incidents", headers, {"tier": "informational", "limit": 50, "offset": 200}),
            ("GET /incidents (all, limit 100)", "GET", f"{BASE_URL}/incidents", headers, {"tier": "all", "limit": 100, "offset": 0}),
            ("GET /incidents/{id} (single detail)", "GET", f"{BASE_URL}/incidents/{sample_incident_id}", headers, None),
            ("GET /incidents/{id}/alerts (child alerts)", "GET", f"{BASE_URL}/incidents/{sample_incident_id}/alerts", headers, None),
            ("GET /incidents/{id}/brief (AI brief + audit log)", "GET", f"{BASE_URL}/incidents/{sample_incident_id}/brief", headers, None),
            
            # Alerts
            ("GET /alerts (first 50)", "GET", f"{BASE_URL}/alerts", None, {"limit": 50, "offset": 0}),
            ("GET /alerts (offset 500, deep)", "GET", f"{BASE_URL}/alerts", None, {"limit": 50, "offset": 500}),
            ("GET /alerts (offset 2000, deep)", "GET", f"{BASE_URL}/alerts", None, {"limit": 50, "offset": 2000}),
            ("GET /alerts (filter by event_type)", "GET", f"{BASE_URL}/alerts", None, {"event_type": "failed_login", "limit": 50}),
            ("GET /alerts (filter by criticality)", "GET", f"{BASE_URL}/alerts", None, {"asset_criticality": "high", "limit": 50}),
            ("GET /alerts/count", "GET", f"{BASE_URL}/alerts/count", None, None),
            ("GET /alerts/{id} (single detail)", "GET", f"{BASE_URL}/alerts/{sample_alert_id}", None, None),
            
            # Metrics
            ("GET /metrics (ground truth & MTTT)", "GET", f"{BASE_URL}/metrics", None, None),
        ]

        print("=" * 95)
        print(f"{'Endpoint':<48} {'Status':<7} {'Avg (ms)':<10} {'Min (ms)':<10} {'Max (ms)':<10} {'Payload':<10}")
        print("-" * 95)

        results = []
        for test in tests:
            res = profile_endpoint(client, test[0], test[1], test[2], headers=test[3], params=test[4])
            results.append(res)
            print(f"{res['endpoint']:<48} {res['status']:<7} {res['avg_ms']:<10.2f} {res['min_ms']:<10.2f} {res['max_ms']:<10.2f} {res['payload_bytes']:<10}")
        print("=" * 95)

if __name__ == "__main__":
    main()
