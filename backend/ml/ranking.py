import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import Base, SessionLocal, engine
from app.models import Alert, Incident

# ==============================================================================
# CONFIGURABLE SEVERITY SCORING WEIGHTS & CONSTANTS
# ==============================================================================
# Asset criticality weights (multiplier = 3)
# Directly reflects asset value to the organization (crown jewels vs peripherals)
ASSET_CRITICALITY_WEIGHTS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

# Event severity weights (multiplier = 2)
# Action severity based on MITRE kill-chain impact (privilege escalation / exfil > routine auth)
EVENT_SEVERITY_WEIGHTS = {
    "privilege_escalation": 5,
    "file_download": 3,
    "failed_login": 2,
    "successful_login": 2,
    "file_access": 2,
    "vpn_connect": 1,
    "password_change": 1,
}

# Volume scaling multiplier (multiplier = 1)
# Natural log scaling prevents high-volume noise attacks from overwhelming high-severity intrusions
ASSET_MULTIPLIER = 3
EVENT_MULTIPLIER = 2
VOLUME_MULTIPLIER = 1


def calculate_score_breakdown(alerts: List[Alert]):
    """Calculates composite severity score and individual explainable components.
    
    SCORING FORMULA RATIONALE:
    --------------------------
    severity_score = (asset_criticality_weight * 3) + (event_severity_weight * 2) + (volume_factor * 1)
    where volume_factor = ln(alert_count + 1)
    
    Returns:
        (severity_score, asset_component, event_component, volume_component, top_asset_factor, top_event_factor)
    """
    if not alerts:
        return 0.0, 0.0, 0.0, 0.0, None, None

    # 1. Asset criticality factor: find max criticality alert
    best_asset_alert = max(
        alerts,
        key=lambda a: ASSET_CRITICALITY_WEIGHTS.get((a.asset_criticality or "").lower(), 1)
    )
    max_asset_weight = ASSET_CRITICALITY_WEIGHTS.get(
        (best_asset_alert.asset_criticality or "").lower(), 1
    )
    asset_comp = round(float(max_asset_weight * ASSET_MULTIPLIER), 2)
    asset_crit = (best_asset_alert.asset_criticality or "unknown").lower()
    top_asset_factor = f"{best_asset_alert.target_asset} ({asset_crit} criticality)"

    # 2. Event severity factor: find max event severity alert
    best_event_alert = max(
        alerts,
        key=lambda a: EVENT_SEVERITY_WEIGHTS.get((a.event_type or "").lower(), 1)
    )
    max_event_weight = EVENT_SEVERITY_WEIGHTS.get(
        (best_event_alert.event_type or "").lower(), 1
    )
    event_comp = round(float(max_event_weight * EVENT_MULTIPLIER), 2)
    top_event_factor = f"{best_event_alert.event_type} (severity {max_event_weight})"

    # 3. Volume factor: logarithmic scaling
    alert_count = len(alerts)
    volume_factor = math.log(alert_count + 1)
    vol_comp = round(float(volume_factor * VOLUME_MULTIPLIER), 2)

    # Composite score: sum of components guaranteed to match exactly
    severity_score = round(asset_comp + event_comp + vol_comp, 2)

    asset_raw_level = (best_asset_alert.asset_criticality or "LOW").upper()
    asset_raw_score = int(max_asset_weight)
    event_type_used = best_event_alert.event_type
    event_raw_score = int(max_event_weight)
    alert_count_used = int(alert_count)

    return (
        severity_score,
        asset_comp,
        event_comp,
        vol_comp,
        top_asset_factor,
        top_event_factor,
        asset_raw_level,
        asset_raw_score,
        event_type_used,
        event_raw_score,
        alert_count_used,
    )


def calculate_severity_score(alerts: List[Alert]) -> float:
    """Calculates composite severity score for an incident based on its alerts."""
    score, *_ = calculate_score_breakdown(alerts)
    return score


def assign_mitre_tag(alerts: List[Alert]) -> Optional[str]:
    """Inspects incident alert behaviors and returns the best matching MITRE ATT&CK technique tag.
    
    Evaluates 8 prioritized rule-based attack patterns (most specific/severe first):
    1. T1567 (Exfiltration Over Web Service): file_download after privilege_escalation on same asset
    2. T1068 (Privilege Escalation): contains privilege_escalation event
    3. T1110 (Brute Force / Password Spraying): >= 10 failed logins from 1 IP across >= 10 usernames
    4. T1110.001 (Brute Force: Password Guessing): repeated failed logins (>= 2) targeted at same username
    5. T1078 (Valid Accounts / Anomalous Login): impossible travel between distinct subnets within 15 min
    6. T1021 (Remote Services / Lateral Movement): same username with successful logins across 3+ assets within 4h
    7. T1005 (Data from Local System):
       - Multi-asset: same user with file_download/access across 2+ assets without priv_esc
       - Single-asset (broadened): 3+ file_download or file_access events on the SAME high-criticality asset
    8. T1098 (Account Manipulation): password_change occurring shortly after failed_login for same user
    None: Genuinely ambiguous clusters stay un-tagged (honest triage precision).
    """
    if not alerts:
        return None

    # Priority 1: Exfiltration Over Web Service / Cloud (T1567)
    priv_esc_alerts = [a for a in alerts if a.event_type == "privilege_escalation"]
    if priv_esc_alerts:
        for pe in priv_esc_alerts:
            has_subsequent_download = any(
                a.event_type == "file_download"
                and a.target_asset == pe.target_asset
                and a.timestamp >= pe.timestamp
                for a in alerts
            )
            if has_subsequent_download:
                return "T1567"

    # Priority 2: Exploitation for Privilege Escalation (T1068)
    if priv_esc_alerts:
        return "T1068"

    # Priority 3: Brute Force: Password Spraying (T1110)
    failed_logins = [a for a in alerts if a.event_type == "failed_login"]
    if len(failed_logins) >= 10:
        ip_to_users: Dict[str, set] = {}
        for a in failed_logins:
            ip_to_users.setdefault(a.source_ip, set()).add(a.username)
        if any(len(users) >= 10 for users in ip_to_users.values()):
            return "T1110"

    # Priority 4: Brute Force: Password Guessing (T1110.001)
    if failed_logins:
        user_failed_counts: Dict[str, int] = {}
        for a in failed_logins:
            user_failed_counts[a.username] = user_failed_counts.get(a.username, 0) + 1
        if any(cnt >= 2 for cnt in user_failed_counts.values()):
            return "T1110.001"

    # Priority 5: Valid Accounts / Anomalous Login (T1078)
    successful_logins = [a for a in alerts if a.event_type == "successful_login"]
    if len(successful_logins) >= 2:
        user_to_logins: Dict[str, List[Alert]] = {}
        for a in successful_logins:
            user_to_logins.setdefault(a.username, []).append(a)

        for user, u_logins in user_to_logins.items():
            if len(u_logins) >= 2:
                sorted_logins = sorted(u_logins, key=lambda x: x.timestamp)
                for i in range(len(sorted_logins) - 1):
                    first = sorted_logins[i]
                    second = sorted_logins[i + 1]
                    time_diff = (second.timestamp - first.timestamp).total_seconds()
                    if time_diff <= 900 and first.source_ip != second.source_ip:
                        ip1_prefix = first.source_ip.split(".")[0]
                        ip2_prefix = second.source_ip.split(".")[0]
                        if ip1_prefix != ip2_prefix:
                            return "T1078"

    # Priority 6: Remote Services / Lateral Movement (T1021)
    if len(successful_logins) >= 3:
        user_to_succ: Dict[str, List[Alert]] = {}
        for a in successful_logins:
            user_to_succ.setdefault(a.username, []).append(a)
        for user, u_logins in user_to_succ.items():
            distinct_assets = set(a.target_asset for a in u_logins)
            if len(distinct_assets) >= 3:
                sorted_l = sorted(u_logins, key=lambda x: x.timestamp)
                if (sorted_l[-1].timestamp - sorted_l[0].timestamp).total_seconds() <= 14400:
                    return "T1021"

    # Priority 7: Data from Local System (T1005)
    if not priv_esc_alerts:
        file_events = [a for a in alerts if a.event_type in ("file_download", "file_access")]
        # 7a: Multi-asset access across 2+ assets
        if len(file_events) >= 2:
            user_to_files: Dict[str, List[Alert]] = {}
            for a in file_events:
                user_to_files.setdefault(a.username, []).append(a)
            for user, u_files in user_to_files.items():
                distinct_assets = set(a.target_asset for a in u_files)
                if len(u_files) >= 2 and len(distinct_assets) >= 2:
                    return "T1005"

        # 7b (broadened): Sustained data access on high-criticality asset:
        # 3+ file_download or file_access events on the SAME high-criticality asset
        high_crit_files = [a for a in file_events if (a.asset_criticality or "").lower() == "high"]
        if len(high_crit_files) >= 3:
            user_asset_counts: Dict[tuple, int] = {}
            asset_counts: Dict[str, int] = {}
            for a in high_crit_files:
                user_asset_counts[(a.username, a.target_asset)] = user_asset_counts.get((a.username, a.target_asset), 0) + 1
                asset_counts[a.target_asset] = asset_counts.get(a.target_asset, 0) + 1
            if any(cnt >= 3 for cnt in user_asset_counts.values()) or any(cnt >= 3 for cnt in asset_counts.values()):
                return "T1005"

    # Priority 8: Account Manipulation (T1098)
    password_changes = [a for a in alerts if a.event_type == "password_change"]
    if password_changes and failed_logins:
        for pc in password_changes:
            has_prior_failed = any(
                fl.username == pc.username and fl.timestamp <= pc.timestamp
                for fl in failed_logins
            )
            if has_prior_failed:
                return "T1098"

    # If none of these match, mitre_tag legitimately stays None / null.
    # This is expected and honest: not every correlated cluster maps to a known attacker technique,
    # and forcing a tag onto genuinely ambiguous data would be dishonest. The goal is better coverage, not 100% coverage.
    return None


def calculate_attack_progression(alerts: List[Alert]):
    """Evaluates chronological kill-chain progression across distinct non-trivial stages.
    
    Stages:
    - Stage 1 (Initial / Credential Access): failed_login, successful_login, vpn_connect, etc.
    - Stage 2 (Privilege Escalation): privilege_escalation, Unauthorized Sudo Access
    - Stage 3 (Objectives / Exfiltration): file_download, Data Exfiltration Attempt, Connection to Honeypot
    
    Categories:
    - Advanced Kill-Chain Detected: Auth -> PrivEsc -> Exfiltration in chronological order
    - Escalation Chain Detected: Auth -> PrivEsc OR PrivEsc -> Exfiltration in chronological order
    - None (Isolated Activity): Routine logins, single-stage activity, or non-escalated sequences
      (e.g., successful_login -> file_access correctly receives None (Isolated Activity)).
    
    Returns:
        (progression_status: str, progression_detail: Optional[str])
    """
    if not alerts or len(alerts) < 2:
        return "None (Isolated Activity)", None

    stage1_types = {
        "failed_login", "successful_login", "vpn_connect",
        "Failed Login Attempt", "Successful Login", "MFA Bypass Attempt", "Geographic Login Anomaly"
    }
    stage2_types = {
        "privilege_escalation", "Unauthorized Sudo Access"
    }
    stage3_types = {
        "file_download", "Data Exfiltration Attempt", "Connection to Honeypot", "Outbound Network Connection"
    }

    sorted_alerts = sorted(alerts, key=lambda a: a.timestamp)

    stage1_times = [a.timestamp for a in sorted_alerts if a.event_type in stage1_types]
    stage2_times = [a.timestamp for a in sorted_alerts if a.event_type in stage2_types]
    stage3_times = [a.timestamp for a in sorted_alerts if a.event_type in stage3_types]

    if stage1_times and stage2_times and stage3_times:
        min_auth = min(stage1_times)
        max_priv = max(stage2_times)
        max_exfil = max(stage3_times)
        if min_auth <= max_priv <= max_exfil:
            return "Advanced Kill-Chain Detected", "Authentication → Privilege Escalation → Exfiltration"

    if stage1_times and stage2_times:
        if min(stage1_times) <= max(stage2_times):
            return "Escalation Chain Detected", "Authentication → Privilege Escalation"

    if stage2_times and stage3_times:
        if min(stage2_times) <= max(stage3_times):
            return "Escalation Chain Detected", "Privilege Escalation → Exfiltration"

    return "None (Isolated Activity)", None


def calculate_correlation_confidence(alerts: List[Alert]):
    """Measures evidence/graph cohesion (how tightly connected the evidence graph is),
    NOT the probability that an incident is malicious.
    
    Returns:
        (confidence_score: float [0.0 - 1.0], confidence_reason: str)
    """
    if not alerts or len(alerts) < 2:
        return 1.0, "High Cohesion (Single-event isolated cluster)"

    users = set(a.username for a in alerts if a.username)
    ips = set(a.source_ip for a in alerts if a.source_ip)
    assets = set(a.target_asset for a in alerts if a.target_asset)

    shared_user = len(users) == 1
    shared_ip = len(ips) == 1
    shared_asset = len(assets) == 1

    # Case 1: Same User, Same IP, Same Asset
    if shared_user and shared_ip and shared_asset:
        return 1.0, "High Cohesion (Identical User, Source IP & Target Asset)"

    # Case 2: High-density single-actor campaign (e.g. Password Spraying)
    if shared_ip and shared_asset and len(alerts) >= 10:
        return 0.95, f"High Cohesion (Campaign Link: Same Source IP & Target Asset across {len(alerts)} alerts)"

    # Case 3: Dual entity match
    if shared_user and shared_ip:
        return 0.85, "Medium Cohesion (Shared User & Source IP)"
    if shared_user and shared_asset:
        return 0.80, "Medium Cohesion (Shared User & Target Asset)"
    if shared_ip and shared_asset:
        return 0.75, "Medium Cohesion (Shared Source IP & Target Asset)"

    # Case 4: Single entity match
    if shared_user:
        return 0.70, "Medium Cohesion (Shared User Identity across varied endpoints)"
    if shared_asset:
        return 0.65, "Medium Cohesion (Target Asset Cohesion)"
    if shared_ip:
        return 0.65, "Medium Cohesion (Source IP Cohesion)"

    # Case 5: Looser / semantic clustering
    return 0.55, "Low Cohesion (Semantic / Behavioral Graph Association)"


def rank_incidents(db: Session):
    """Calculates severity scores, assigns MITRE tags, ranks incidents, and commits updates."""
    incidents = db.query(Incident).all()
    if not incidents:
        print("No incidents found in database to rank.")
        return

    print(f"Scoring and tagging {len(incidents)} incidents...")

    scored_data = []
    for inc in incidents:
        alerts = db.query(Alert).filter(Alert.incident_id == inc.incident_id).all()
        (
            score,
            asset_comp,
            event_comp,
            vol_comp,
            top_asset,
            top_event,
            asset_raw_level,
            asset_raw_score,
            event_type_used,
            event_raw_score,
            alert_count_used,
        ) = calculate_score_breakdown(alerts)
        mitre_tag = assign_mitre_tag(alerts)
        progression, prog_detail = calculate_attack_progression(alerts)
        conf_score, conf_reason = calculate_correlation_confidence(alerts)
        scored_data.append(
            (
                inc,
                score,
                asset_comp,
                event_comp,
                vol_comp,
                top_asset,
                top_event,
                asset_raw_level,
                asset_raw_score,
                event_type_used,
                event_raw_score,
                alert_count_used,
                mitre_tag,
                len(alerts),
                progression,
                prog_detail,
                conf_score,
                conf_reason,
            )
        )

    # Sort descending by severity_score, secondary sort by alert_count descending
    scored_data.sort(key=lambda item: (item[1], item[13]), reverse=True)

    # Compute dynamic severity threshold (90th percentile of severity_score across all incidents)
    import numpy as np
    scores = [item[1] for item in scored_data]
    p90_threshold = float(np.percentile(scores, 90)) if scores else 0.0
    print(f"Computed 90th-percentile dynamic severity threshold: {p90_threshold:.2f}")

    actionable_count = 0
    informational_count = 0

    # Assign ranks: 1 = most severe, and classify confidence tier
    for rank_idx, item in enumerate(scored_data, start=1):
        (
            inc,
            score,
            asset_comp,
            event_comp,
            vol_comp,
            top_asset,
            top_event,
            asset_raw_level,
            asset_raw_score,
            event_type_used,
            event_raw_score,
            alert_count_used,
            mitre_tag,
            alert_count,
            progression,
            prog_detail,
            conf_score,
            conf_reason,
        ) = item

        inc.severity_score = score
        inc.severity_rank = rank_idx
        inc.mitre_tag = mitre_tag
        inc.attack_progression = progression
        inc.progression_detail = prog_detail
        inc.correlation_confidence = conf_score
        inc.confidence_reason = conf_reason
        inc.score_asset_component = asset_comp
        inc.score_event_component = event_comp
        inc.score_volume_component = vol_comp
        inc.top_asset_factor = top_asset
        inc.top_event_factor = top_event
        inc.asset_raw_level = asset_raw_level
        inc.asset_raw_score = asset_raw_score
        inc.event_type_used = event_type_used
        inc.event_raw_score = event_raw_score
        inc.alert_count_used = alert_count_used

        # Tightened Actionable Rule:
        # Require a confirmed attacker technique (mitre_tag IS NOT NULL)
        # OR extreme composite severity (>= 90th percentile).
        if mitre_tag is not None or score >= p90_threshold:
            inc.confidence_tier = "actionable"
            actionable_count += 1
        else:
            inc.confidence_tier = "informational"
            informational_count += 1

    db.commit()
    print("Severity scores, ranks, MITRE tags, score breakdowns, and confidence tiers committed to database.")
    print(f"Triage Tiering: {actionable_count} actionable incidents, {informational_count} informational incidents.")

    # Print summary table
    print("\n================ INCIDENT RANKING SUMMARY ================")
    print(f"{'Rank':<6} {'Score':<8} {'Tier':<14} {'MITRE':<10} {'Alerts':<8} {'Incident ID'}")
    print("-" * 80)
    for item in scored_data[:15]:
        inc, score = item[0], item[1]
        mitre_tag, count = item[12], item[13]
        tag_str = mitre_tag if mitre_tag else "-"
        print(f"#{inc.severity_rank:<5} {score:<8.2f} {inc.confidence_tier:<14} {tag_str:<10} {count:<8} {inc.incident_id}")
    if len(scored_data) > 15:
        print(f"... and {len(scored_data) - 15} more incidents ranked.")
    print("==========================================================\n")


def main():
    db = SessionLocal()
    try:
        rank_incidents(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
