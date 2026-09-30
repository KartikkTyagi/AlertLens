"""
AlertLens Dataset V2 Addition Generator & Inserter
==================================================
Generates exactly 431 alerts to expand Dataset V1 (2,569 alerts) -> V2 (3,000 alerts):
  - Category A: 379 benign background telemetry alerts
  - Category B: 44 benign correlated operational alerts (B1: 22 svc_backup, B2: 22 svc_deploy)
  - Category C: 8 planted Scenario D lateral movement alerts (dlee, 10.0.1.25)

Deterministic seed: 42
Preserves all 2,569 existing V1 alerts untouched.
"""

import json
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Tuple

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models import Alert
from ml.data_generator import ASSETS, FILENAMES, INTERNAL_IPS, USERNAMES, generate_raw_message

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

def generate_category_c_scenario_d() -> List[Dict]:
    """Generate exactly 8 alerts for Scenario D (lateral movement) as specified in DATASET_V2_DESIGN.md."""
    t0 = datetime(2026, 9, 22, 14, 10, 0, tzinfo=timezone.utc)
    ip = "10.0.1.25"
    user = "dlee"

    steps = [
        (
            0,
            "successful_login",
            "dev-sandbox-01",
            "low",
            f"Interactive logon session established for user {user} from {ip} on dev-sandbox-01 via SSH",
        ),
        (
            150,
            "file_access",
            "dev-sandbox-01",
            "low",
            f"Read access granted for file api_keys_draft.txt to user {user} from IP {ip} on dev-sandbox-01",
        ),
        (
            300,
            "successful_login",
            "ci-cd-runner-01",
            "medium",
            f"Remote service SSH session opened by user {user} from {ip} to ci-cd-runner-01",
        ),
        (
            450,
            "file_access",
            "ci-cd-runner-01",
            "medium",
            f"User {user} accessed file pipeline_secret.yaml on asset ci-cd-runner-01 from {ip}",
        ),
        (
            600,
            "successful_login",
            "git-internal-01",
            "medium",
            f"User {user} logged in successfully from {ip} to git-internal-01 via Kerberos/SSH",
        ),
        (
            750,
            "file_access",
            "git-internal-01",
            "medium",
            f"Shared storage access: {user} opened schema_dump.sql on network asset git-internal-01",
        ),
        (
            900,
            "successful_login",
            "customer-pii-db",
            "high",
            f"Session initiated: user {user} verified from source {ip} on crown-jewel customer-pii-db",
        ),
        (
            1050,
            "file_access",
            "customer-pii-db",
            "high",
            f"User {user} accessed database export customer_records_2026.csv on asset customer-pii-db from {ip}",
        ),
    ]

    records = []
    for offset_sec, ev_type, asset, crit, msg in steps:
        ts = t0 + timedelta(seconds=offset_sec)
        records.append({
            "alert_id": str(uuid.uuid4()),
            "timestamp": ts,
            "source_ip": ip,
            "username": user,
            "event_type": ev_type,
            "target_asset": asset,
            "asset_criticality": crit,
            "raw_message": msg,
            "category": "C_scenario_d",
        })
    return records


def generate_category_b_operational() -> List[Dict]:
    """Generate exactly 44 alerts for operational batches:
    B1: 22 alerts (svc_backup, 10.0.4.15) between 02:00:00 and 02:35:00 on 2026-09-22
    B2: 22 alerts (svc_deploy, 10.0.10.12) between 04:00:00 and 04:28:00 on 2026-09-22
    Event breakdown across B:
      14 successful_login (7 in B1, 7 in B2)
      20 file_access (10 in B1, 10 in B2)
      6 file_download (3 in B1, 3 in B2)
      4 vpn_connect (2 in B1, 2 in B2)
    """
    records = []

    # Sequence B1: Automated Nightly DB Backup & Replication
    b1_start = datetime(2026, 9, 22, 2, 0, 0, tzinfo=timezone.utc)
    b1_user = "svc_backup"
    b1_ip = "10.0.4.15"
    b1_assets = ["pki-root-ca", "finance-db-01", "customer-pii-db", "backup-archive-cold"]

    # 22 events scheduled across 35 minutes (~95 seconds interval)
    # 7 logins, 10 file_access, 3 file_download, 2 vpn_connect
    b1_event_types = (
        ["vpn_connect"] * 2 +
        ["successful_login"] * 7 +
        ["file_access"] * 10 +
        ["file_download"] * 3
    )
    # deterministic order representing backup workflow: VPN connect -> logins -> file_access -> download
    b1_event_types_ordered = [
        "vpn_connect", "successful_login", "file_access", "file_access",
        "successful_login", "file_access", "file_download",
        "successful_login", "file_access", "file_access", "file_download",
        "successful_login", "file_access", "file_access",
        "successful_login", "file_access", "file_download",
        "successful_login", "file_access", "file_access",
        "vpn_connect", "successful_login"
    ]

    for idx, ev_type in enumerate(b1_event_types_ordered):
        offset = idx * 95 + random.randint(0, 5)
        ts = b1_start + timedelta(seconds=offset)
        asset = b1_assets[idx % len(b1_assets)]
        crit = ASSETS[asset]
        msg = generate_raw_message(ev_type, b1_user, b1_ip, asset)
        records.append({
            "alert_id": str(uuid.uuid4()),
            "timestamp": ts,
            "source_ip": b1_ip,
            "username": b1_user,
            "event_type": ev_type,
            "target_asset": asset,
            "asset_criticality": crit,
            "raw_message": msg,
            "category": "B1_svc_backup",
        })

    # Sequence B2: Scheduled Configuration Management Rollout
    b2_start = datetime(2026, 9, 22, 4, 0, 0, tzinfo=timezone.utc)
    b2_user = "svc_deploy"
    b2_ip = "10.0.10.12"
    b2_assets = ["dev-sandbox-01", "dev-sandbox-02", "ci-cd-runner-01"]

    b2_event_types_ordered = [
        "vpn_connect", "successful_login", "file_access", "file_access",
        "successful_login", "file_access", "file_download",
        "successful_login", "file_access", "file_access", "file_download",
        "successful_login", "file_access", "file_access",
        "successful_login", "file_access", "file_download",
        "successful_login", "file_access", "file_access",
        "vpn_connect", "successful_login"
    ]

    for idx, ev_type in enumerate(b2_event_types_ordered):
        offset = idx * 75 + random.randint(0, 5)
        ts = b2_start + timedelta(seconds=offset)
        asset = b2_assets[idx % len(b2_assets)]
        crit = ASSETS[asset]
        msg = generate_raw_message(ev_type, b2_user, b2_ip, asset)
        records.append({
            "alert_id": str(uuid.uuid4()),
            "timestamp": ts,
            "source_ip": b2_ip,
            "username": b2_user,
            "event_type": ev_type,
            "target_asset": asset,
            "asset_criticality": crit,
            "raw_message": msg,
            "category": "B2_svc_deploy",
        })

    return records


def generate_category_a_background() -> List[Dict]:
    """Generate exactly 379 benign background alerts matching design counts:
    - successful_login: 130
    - failed_login: 80
    - file_download: 60
    - file_access: 55
    - vpn_connect: 35
    - password_change: 19
    Total: 379 alerts
    """
    event_distribution = (
        ["successful_login"] * 130 +
        ["failed_login"] * 80 +
        ["file_download"] * 60 +
        ["file_access"] * 55 +
        ["vpn_connect"] * 35 +
        ["password_change"] * 19
    )
    assert len(event_distribution) == 379

    # Timeline bounds matching canonical V1 database (2026-09-21 21:00:00 to 2026-09-23 22:00:00)
    start_time = datetime(2026, 9, 21, 21, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 9, 23, 22, 0, 0, tzinfo=timezone.utc)
    total_seconds = int((end_time - start_time).total_seconds())

    # Exclude "dlee", "svc_backup", "svc_deploy" from background pool to prevent unintended correlation
    candidate_users = [u for u in USERNAMES if u not in ("dlee", "svc_backup", "svc_deploy")]
    # Exclude 10.0.1.25, 10.0.4.15, 10.0.10.12
    candidate_ips = [ip for ip in INTERNAL_IPS if ip not in ("10.0.1.25", "10.0.4.15", "10.0.10.12")]
    asset_keys = list(ASSETS.keys())

    records = []
    # Shuffle event distribution for natural spread
    random.shuffle(event_distribution)

    for ev_type in event_distribution:
        offset = random.randint(0, total_seconds)
        ts = start_time + timedelta(seconds=offset)

        user = random.choice(candidate_users)
        ip = random.choice(candidate_ips)
        asset = random.choice(asset_keys)
        crit = ASSETS[asset]
        msg = generate_raw_message(ev_type, user, ip, asset)

        records.append({
            "alert_id": str(uuid.uuid4()),
            "timestamp": ts,
            "source_ip": ip,
            "username": user,
            "event_type": ev_type,
            "target_asset": asset,
            "asset_criticality": crit,
            "raw_message": msg,
            "category": "A_background",
        })

    return records


def validate_and_generate():
    """Generates all 431 alerts and runs pre-insert validation."""
    print("=" * 70)
    print("ALERTLENS DATASET V2 GENERATION & VALIDATION")
    print("=" * 70)

    cat_a = generate_category_a_background()
    cat_b = generate_category_b_operational()
    cat_c = generate_category_c_scenario_d()

    all_new = cat_a + cat_b + cat_c
    print(f"Generated Category A (Background):   {len(cat_a)} alerts")
    print(f"Generated Category B (Operational):  {len(cat_b)} alerts (B1: 22, B2: 22)")
    print(f"Generated Category C (Scenario D):   {len(cat_c)} alerts")
    print(f"Total new alerts:                    {len(all_new)} alerts")

    assert len(all_new) == 431, f"Expected 431 alerts, got {len(all_new)}"

    # Event type breakdown verification
    counts = {}
    for r in all_new:
        et = r["event_type"]
        counts[et] = counts.get(et, 0) + 1

    expected_counts = {
        "successful_login": 148,
        "failed_login": 80,
        "file_download": 66,
        "file_access": 79,
        "vpn_connect": 39,
        "password_change": 19,
    }
    print("\nEvent type breakdown check:")
    for et, exp in expected_counts.items():
        actual = counts.get(et, 0)
        status = "OK" if actual == exp else "MISMATCH"
        print(f"  {et:20s}: {actual:3d} (expected {exp:3d}) [{status}]")
        assert actual == exp, f"Mismatch for {et}: {actual} != {exp}"

    # Verify UUID uniqueness within new records
    ids = set(r["alert_id"] for r in all_new)
    assert len(ids) == 431, "Duplicate alert_id found within generated alerts"

    # Verify 5-tuple deduplication within new records
    tuples_new = set(
        (r["timestamp"], r["source_ip"], r["username"], r["event_type"], r["target_asset"])
        for r in all_new
    )
    assert len(tuples_new) == 431, "Duplicate 5-tuple detected within generated alerts"

    # Query DB to ensure no collisions with existing 2,569 alerts
    print("\nChecking against existing database records...")
    db = SessionLocal()
    try:
        existing_alerts = db.query(Alert).all()
        print(f"Existing alerts in DB: {len(existing_alerts)}")
        assert len(existing_alerts) == 2569, f"Expected 2569 existing alerts, got {len(existing_alerts)}"

        existing_ids = set(a.alert_id for a in existing_alerts)
        existing_tuples = set(
            (a.timestamp, a.source_ip, a.username, a.event_type, a.target_asset)
            for a in existing_alerts
        )

        # Check ID collision
        id_collisions = ids.intersection(existing_ids)
        assert len(id_collisions) == 0, f"ID collision with existing DB: {id_collisions}"

        # Check 5-tuple collision
        tuple_collisions = tuples_new.intersection(existing_tuples)
        assert len(tuple_collisions) == 0, f"5-tuple collision with existing DB: {tuple_collisions}"

        print("Validation checks PASSED:")
        print("  - Exactly 431 alerts generated")
        print("  - Event distribution matches DATASET_V2_DESIGN.md specifications exactly")
        print("  - Zero duplicate UUIDs")
        print("  - Zero 5-tuple collisions within new data")
        print("  - Zero 5-tuple collisions with existing 2,569 database alerts")

        return all_new, cat_c
    finally:
        db.close()


def insert_records(all_new: List[Dict], cat_c: List[Dict]):
    """Inserts the 431 records into PostgreSQL and updates ground_truth.json."""
    db = SessionLocal()
    try:
        print("\nInserting 431 alerts into PostgreSQL...")
        alert_models = []
        for r in all_new:
            alert_models.append(Alert(
                alert_id=r["alert_id"],
                timestamp=r["timestamp"],
                source_ip=r["source_ip"],
                username=r["username"],
                event_type=r["event_type"],
                target_asset=r["target_asset"],
                asset_criticality=r["asset_criticality"],
                raw_message=r["raw_message"],
                incident_id=None
            ))

        db.bulk_save_objects(alert_models)
        db.commit()
        print("PostgreSQL commit complete.")

        total_in_db = db.query(Alert).count()
        print(f"Total alerts in database now: {total_in_db}")
        assert total_in_db == 3000, f"Expected 3000 alerts, got {total_in_db}"

        # Update ground_truth.json with Scenario D
        gt_file = backend_dir / "data" / "ground_truth.json"
        with open(gt_file, "r", encoding="utf-8") as f:
            gt = json.load(f)

        # Check existing scenarios are preserved
        assert "scenario_a_password_spraying" in gt and len(gt["scenario_a_password_spraying"]) == 50
        assert "scenario_b_impossible_travel" in gt and len(gt["scenario_b_impossible_travel"]) == 2
        assert "scenario_c_privilege_escalation" in gt and len(gt["scenario_c_privilege_escalation"]) == 6

        scenario_d_ids = [r["alert_id"] for r in cat_c]
        assert len(scenario_d_ids) == 8

        gt["scenario_d_lateral_movement"] = scenario_d_ids

        with open(gt_file, "w", encoding="utf-8") as f:
            json.dump(gt, f, indent=2)

        print(f"Updated {gt_file} with scenario_d_lateral_movement ({len(scenario_d_ids)} alerts).")
        print(f"Total scenarios in ground truth: {len(gt)}")
        print(f"Total ground truth alerts: {sum(len(v) for v in gt.values())}")
        print("\nDATASET V2 GENERATION & INSERTION SUCCESSFUL.")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    new_alerts, scenario_d_alerts = validate_and_generate()
    # If run with --commit, execute the insert
    if "--commit" in sys.argv:
        insert_records(new_alerts, scenario_d_alerts)
    else:
        print("\nDry run complete. Run with --commit to insert into PostgreSQL and update ground_truth.json.")
