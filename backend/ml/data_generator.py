import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add backend directory to sys.path to allow running both from backend/ or repo root
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import Base, SessionLocal, engine
from app.models import Alert

# Fixed pools for realism
USERNAMES = [
    "jsmith", "agupta", "mkhan", "schen", "dlee", "mrodriguez", "ebrown", "jwilson",
    "ataylor", "landerson", "cthomas", "jjackson", "swhite", "hharris", "smartin",
    "jthompson", "bgarcia", "rmartinez", "crobinson", "kclark", "rrodriguez", "llewis",
    "mlee", "dwalker", "jhall", "aallen", "tyoung", "bhernandez", "sking", "mwright",
    "plopez", "chill", "jscott", "egreen", "radams", "bbaker", "mgonzalez", "nnelson",
    "ccarter", "wmitchell", "pperez", "croberts", "dturner", "ephillips", "ccampbell",
    "aparker", "fevans", "gedwards", "ccollins", "rreyes", "tstewart", "mmorris",
    "amorales", "dmurphy", "ccook", "jrogers", "ggutierrez", "jortiz", "mmorgan",
    "jcooper", "epeterson", "hbailey", "rreed", "kkelly", "jhoward", "ramos",
    "kcox", "dward", "trichardson", "awatson", "jbrooks", "cchavez", "awood",
    "djames", "mbennett", "gray", "mmendoza", "cruiz", "jhughes", "cprice",
    "aalvarez", "jcastillo", "ssanders", "kpatel", "gmyers", "along", "rross",
    "ffoster", "jjimenez", "bpowell", "tjenkins", "jperry", "rrussell", "esullivan",
    "bbell", "ccoleman", "bbutler", "ghenderson", "tbarnes", "lgonzales"
]

ASSETS = {
    # High criticality
    "finance-db-01": "high",
    "finance-db-02": "high",
    "ceo-laptop": "high",
    "cfo-workstation": "high",
    "auth-server-primary": "high",
    "customer-pii-db": "high",
    "core-switch-01": "high",
    "pki-root-ca": "high",
    # Medium criticality
    "web-server-01": "medium",
    "web-server-02": "medium",
    "web-server-03": "medium",
    "app-server-01": "medium",
    "app-server-02": "medium",
    "mail-gateway-01": "medium",
    "vpn-gateway-01": "medium",
    "vpn-gateway-02": "medium",
    "file-share-corp": "medium",
    "git-internal-01": "medium",
    "ci-cd-runner-01": "medium",
    "monitoring-srv-01": "medium",
    # Low criticality
    "printer-hr-02": "low",
    "printer-marketing-01": "low",
    "printer-exec-01": "low",
    "dev-sandbox-01": "low",
    "dev-sandbox-02": "low",
    "guest-wifi-ap-01": "low",
    "guest-wifi-ap-02": "low",
    "cafeteria-kiosk-01": "low",
    "reception-tablet-01": "low",
    "backup-archive-cold": "low",
}

INTERNAL_IPS = [
    f"10.0.{subnet}.{host}"
    for subnet in [1, 2, 4, 10]
    for host in range(10, 35)
] + [
    f"192.168.1.{host}" for host in range(100, 125)
]

FILENAMES = [
    "quarterly_report.xlsx", "client_roster.csv", "project_specs.pdf",
    "network_topology.vsdx", "api_keys_draft.txt", "budget_2026.xlsx",
    "employee_handbook.pdf", "presentation_all_hands.pptx", "schema_dump.sql"
]


def generate_raw_message(event_type: str, username: str, source_ip: str, asset: str) -> str:
    filename = random.choice(FILENAMES)
    filesize = random.randint(12, 8500)
    
    templates = {
        "failed_login": [
            f"Failed login attempt for user {username} from {source_ip} on {asset}: invalid credentials",
            f"Authentication failure for user {username} from {source_ip} on {asset}: password mismatch",
            f"Logon failure detected: user {username} source IP {source_ip} targeting {asset}",
            f"Unsuccessful authentication attempt for account {username} from host {source_ip} on {asset}",
        ],
        "successful_login": [
            f"User {username} logged in successfully from {source_ip} to {asset} via SSH/Kerberos",
            f"Successful authentication for {username} from IP {source_ip} on system {asset}",
            f"Interactive logon session established for user {username} from {source_ip} on {asset}",
            f"Session initiated: user {username} verified from source {source_ip} on {asset}",
        ],
        "file_download": [
            f"File download event: {filename} transferred to {source_ip} by user {username} from {asset}",
            f"Data transfer: user {username} downloaded file {filename} from {asset} to {source_ip}",
            f"Outbound file retrieval of {filename} from {asset} initiated by {username} at {source_ip}",
            f"User {username} downloaded document {filename} ({filesize} KB) from {asset}",
        ],
        "password_change": [
            f"User {username} initiated password change request from {source_ip} on {asset}",
            f"Account password successfully updated for {username} via host {source_ip} on {asset}",
            f"Self-service password reset operation completed for user {username} from client {source_ip}",
        ],
        "vpn_connect": [
            f"VPN tunnel established for user {username} from client IP {source_ip} to gateway {asset}",
            f"Remote access VPN connection opened by user {username} from {source_ip} via {asset}",
            f"Secure VPN session started: account {username} assigned from {source_ip} connecting to {asset}",
        ],
        "file_access": [
            f"User {username} accessed file {filename} on asset {asset} from {source_ip}",
            f"Read access granted for file {filename} to user {username} from IP {source_ip} on {asset}",
            f"Shared storage access: {username} opened {filename} on network asset {asset}",
            f"File access event logged: {username} viewed {filename} on {asset}",
        ],
        "privilege_escalation": [
            f"Privilege escalation event: user {username} elevated rights to root/admin on {asset} from {source_ip}",
            f"Administrative role switch detected: {username} invoked sudo/su privilege escalation on {asset}",
        ],
    }

    return random.choice(templates[event_type])


def generate_dataset(num_noise_alerts: int = 2500):
    """Generates synthetic noise alerts and 3 planted attack scenarios."""
    alerts = []
    ground_truth = {
        "scenario_a_password_spraying": [],
        "scenario_b_impossible_travel": [],
        "scenario_c_privilege_escalation": []
    }

    # Reference base time: 48-hour window up to now
    base_end_time = datetime.now(timezone.utc)
    base_start_time = base_end_time - timedelta(hours=48)
    total_seconds = int((base_end_time - base_start_time).total_seconds())

    asset_names = list(ASSETS.keys())
    noise_event_types = [
        "failed_login", "successful_login", "file_download",
        "password_change", "vpn_connect", "file_access"
    ]
    event_weights = [0.20, 0.35, 0.15, 0.05, 0.10, 0.15]

    # 1. Generate Noise Alerts (~2,500)
    for _ in range(num_noise_alerts):
        alert_id = str(uuid.uuid4())
        event_type = random.choices(noise_event_types, weights=event_weights)[0]
        user = random.choice(USERNAMES)
        source_ip = random.choice(INTERNAL_IPS)
        asset = random.choice(asset_names)
        criticality = ASSETS[asset]
        raw_message = generate_raw_message(event_type, user, source_ip, asset)
        
        # Random timestamp spread across 48h
        offset_seconds = random.randint(0, total_seconds)
        timestamp = base_start_time + timedelta(seconds=offset_seconds)

        alerts.append(Alert(
            alert_id=alert_id,
            timestamp=timestamp,
            source_ip=source_ip,
            username=user,
            event_type=event_type,
            target_asset=asset,
            asset_criticality=criticality,
            raw_message=raw_message,
            incident_id=None
        ))

    # 2. Plant Scenario A: Password spraying (~50 failed logins, 1 source IP, many users, within 15 mins)
    spray_ip = "198.51.100.45"  # External attacker IP
    spray_asset = "auth-server-primary"
    spray_start = base_start_time + timedelta(hours=14)
    # Pick 50 distinct usernames
    spray_users = random.sample(USERNAMES, 50)
    
    for i, target_user in enumerate(spray_users):
        alert_id = str(uuid.uuid4())
        # Spread across 15 minutes (900 seconds)
        offset_sec = (i * 900) // len(spray_users) + random.randint(0, 5)
        timestamp = spray_start + timedelta(seconds=offset_sec)
        raw_msg = f"Failed login attempt for user {target_user} from {spray_ip} on {spray_asset}: invalid credentials"

        alerts.append(Alert(
            alert_id=alert_id,
            timestamp=timestamp,
            source_ip=spray_ip,
            username=target_user,
            event_type="failed_login",
            target_asset=spray_asset,
            asset_criticality=ASSETS[spray_asset],
            raw_message=raw_msg,
            incident_id=None
        ))
        ground_truth["scenario_a_password_spraying"].append(alert_id)

    # 3. Plant Scenario B: Impossible travel (1 username, 2 logins from far apart IPs within 5 mins)
    travel_user = "ebrown"
    travel_time_1 = base_start_time + timedelta(hours=22, minutes=10)
    travel_time_2 = travel_time_1 + timedelta(minutes=3, seconds=45)

    alert_b1_id = str(uuid.uuid4())
    alert_b1 = Alert(
        alert_id=alert_b1_id,
        timestamp=travel_time_1,
        source_ip="198.51.100.12",  # US-East
        username=travel_user,
        event_type="successful_login",
        target_asset="vpn-gateway-01",
        asset_criticality=ASSETS["vpn-gateway-01"],
        raw_message=f"Interactive logon session established for user {travel_user} from 198.51.100.12 (US-East) on vpn-gateway-01",
        incident_id=None
    )
    alerts.append(alert_b1)
    ground_truth["scenario_b_impossible_travel"].append(alert_b1_id)

    alert_b2_id = str(uuid.uuid4())
    alert_b2 = Alert(
        alert_id=alert_b2_id,
        timestamp=travel_time_2,
        source_ip="203.0.113.88",  # APAC-Tokyo
        username=travel_user,
        event_type="successful_login",
        target_asset="vpn-gateway-02",
        asset_criticality=ASSETS["vpn-gateway-02"],
        raw_message=f"Interactive logon session established for user {travel_user} from 203.0.113.88 (APAC-Tokyo) on vpn-gateway-02",
        incident_id=None
    )
    alerts.append(alert_b2)
    ground_truth["scenario_b_impossible_travel"].append(alert_b2_id)

    # 4. Plant Scenario C: Privilege escalation chain (1 user, escalating 6 alerts, same high-criticality asset, short window)
    chain_user = "mrodriguez"
    chain_asset = "finance-db-01"  # High criticality
    chain_ip = "10.0.1.42"
    chain_start = base_start_time + timedelta(hours=31, minutes=15)

    chain_steps = [
        (0, "failed_login", f"Failed login attempt for user {chain_user} from {chain_ip} on {chain_asset}: password mismatch"),
        (180, "successful_login", f"User {chain_user} logged in successfully from {chain_ip} to {chain_asset} via SSH/Kerberos"),
        (360, "file_access", f"User {chain_user} accessed file /etc/shadow on asset {chain_asset} from {chain_ip}"),
        (540, "privilege_escalation", f"Administrative role switch detected: {chain_user} invoked sudo/su privilege escalation on {chain_asset}"),
        (720, "file_access", f"Shared storage access: {chain_user} opened q4_financials_confidential.tar.gz on network asset {chain_asset}"),
        (900, "file_download", f"File download event: q4_financials_confidential.tar.gz transferred to {chain_ip} by user {chain_user} from {chain_asset}")
    ]

    for offset_sec, ev_type, msg in chain_steps:
        alert_id = str(uuid.uuid4())
        timestamp = chain_start + timedelta(seconds=offset_sec)
        alerts.append(Alert(
            alert_id=alert_id,
            timestamp=timestamp,
            source_ip=chain_ip,
            username=chain_user,
            event_type=ev_type,
            target_asset=chain_asset,
            asset_criticality=ASSETS[chain_asset],
            raw_message=msg,
            incident_id=None
        ))
        ground_truth["scenario_c_privilege_escalation"].append(alert_id)

    return alerts, ground_truth


def main():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    print("Generating synthetic alert dataset...")
    alerts, ground_truth = generate_dataset(num_noise_alerts=2500)

    db = SessionLocal()
    try:
        print(f"Writing {len(alerts)} alerts to database...")
        db.bulk_save_objects(alerts)
        db.commit()
        print("Database commit successful.")
    except Exception as e:
        db.rollback()
        print(f"Error inserting alerts: {e}")
        raise
    finally:
        db.close()

    # Save ground_truth.json to backend/data/ground_truth.json
    data_dir = backend_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    gt_file = data_dir / "ground_truth.json"

    with open(gt_file, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"Ground truth written to: {gt_file}")
    print("\n--- Generation Summary ---")
    print(f"Total alerts generated: {len(alerts)}")
    print(f"Noise alerts: 2500")
    print(f"Scenario A (Password Spraying): {len(ground_truth['scenario_a_password_spraying'])} alerts")
    print(f"Scenario B (Impossible Travel): {len(ground_truth['scenario_b_impossible_travel'])} alerts")
    print(f"Scenario C (Privilege Escalation): {len(ground_truth['scenario_c_privilege_escalation'])} alerts")


if __name__ == "__main__":
    main()
