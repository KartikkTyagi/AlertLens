import json
import os
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

import networkx as nx
import numpy as np
from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import Base, SessionLocal, engine
from app.models import Alert, Incident
from ml.embeddings import generate_embeddings

# ==============================================================================
# CONFIGURABLE CLUSTERING HYPERPARAMETERS (TIGHTENED ANTI-PERCOLATION LOGIC)
# ==============================================================================
# Rule-based correlation window for standalone IP or User signals (minutes)
RULE_TIME_WINDOW_MINUTES = 15

# Tightened time window when shared asset is involved (minutes)
ASSET_TIME_WINDOW_MINUTES = 10

# Semantic correlation window (minutes)
SEMANTIC_TIME_WINDOW_MINUTES = 30

# Cosine similarity threshold for semantic edges between normalized alert embeddings
# Raised from 0.80 to 0.90 to prevent loosely-related events from chaining
SEMANTIC_SIMILARITY_THRESHOLD = 0.90

# Minimum number of correlated alerts required to constitute an incident
MIN_CLUSTER_SIZE = 2

# Hard cap threshold: components larger than this are automatically split
MAX_COMPONENT_SIZE_BEFORE_SPLIT = 25

# Time gap threshold for splitting large components by primary entity (minutes)
SPLIT_TIME_GAP_MINUTES = 20

# Sanity check threshold for warning log
SANITY_MAX_ALERT_WARNING = 100


def build_similarity_graph(
    alerts: List[Alert],
    embeddings_map: Dict[str, np.ndarray],
    strict_mode: bool = False,
) -> nx.Graph:
    """Builds a graph combining deterministic rule-based edges with semantic similarity edges.
    
    ANTI-PERCOLATION DESIGN:
    ------------------------
    1. Deterministic Rule Edges (Local Context):
       - same_ip OR same_user within 15 minutes are valid standalone signals.
       - same_asset is NEVER sufficient on its own across broad windows.
         Requires (same_asset AND same_user) within 15 minutes, or
         (same_asset AND time <= 10 minutes) in standard mode.
         In strict_mode (used during sub-cluster refinement), asset-alone is disallowed.
    2. Semantic Embeddings Edges (Behavioral Context):
       - Cosine similarity >= 0.90 within 30 minutes.
       - MUST share at least one weak entity signal (same_ip, same_user, OR same_asset).
         Pure semantic edges without any shared entity are prohibited.
    """
    G = nx.Graph()

    for alert in alerts:
        G.add_node(alert.alert_id)

    n = len(alerts)
    if n < 2:
        return G

    # Precalculate timestamps
    timestamps = [a.timestamp for a in alerts]
    rule_window = timedelta(minutes=RULE_TIME_WINDOW_MINUTES)
    asset_window = timedelta(minutes=ASSET_TIME_WINDOW_MINUTES)
    semantic_window = timedelta(minutes=SEMANTIC_TIME_WINDOW_MINUTES)
    max_window = max(rule_window, semantic_window)

    rule_edge_count = 0
    semantic_edge_count = 0

    for i in range(n):
        a_i = alerts[i]
        t_i = timestamps[i]
        emb_i = embeddings_map[a_i.alert_id]

        for j in range(i + 1, n):
            a_j = alerts[j]
            t_j = timestamps[j]
            time_diff = t_j - t_i

            # Since alerts are sorted by timestamp, break when time difference exceeds maximum window
            if time_diff > max_window:
                break

            same_ip = a_i.source_ip == a_j.source_ip
            same_user = a_i.username == a_j.username
            same_asset = a_i.target_asset == a_j.target_asset

            # 1. Rule-based Edge Check
            is_rule_edge = False
            if (same_ip or same_user) and time_diff <= rule_window:
                is_rule_edge = True
            elif same_asset and same_user and time_diff <= rule_window:
                is_rule_edge = True
            elif not strict_mode and same_asset and time_diff <= asset_window:
                is_rule_edge = True

            if is_rule_edge:
                G.add_edge(a_i.alert_id, a_j.alert_id, edge_type="rule")
                rule_edge_count += 1
                continue

            # 2. Semantic Edge Check
            # Requires cosine similarity >= 0.90 AND at least one shared entity signal
            if time_diff <= semantic_window and (same_ip or same_user or same_asset):
                emb_j = embeddings_map[a_j.alert_id]
                cos_sim = float(np.dot(emb_i, emb_j))
                if cos_sim >= SEMANTIC_SIMILARITY_THRESHOLD:
                    G.add_edge(a_i.alert_id, a_j.alert_id, edge_type="semantic")
                    semantic_edge_count += 1

    return G


def split_large_component(
    comp_alerts: List[Alert],
    embeddings_map: Dict[str, np.ndarray],
) -> List[List[str]]:
    """Splits an oversized component (> 25 alerts) to prevent graph percolation.
    
    1. First tries re-clustering with strict anti-percolation thresholds.
    2. If still exceeding MAX_COMPONENT_SIZE_BEFORE_SPLIT, falls back to grouping by 
       primary entity (source_ip) and splitting by time gaps > 20 minutes.
    """
    comp_alerts_sorted = sorted(comp_alerts, key=lambda a: a.timestamp)
    
    # Pass 1: Try strict re-clustering on this subgroup
    strict_G = build_similarity_graph(comp_alerts_sorted, embeddings_map, strict_mode=True)
    strict_comps = list(nx.connected_components(strict_G))
    
    # Check if strict re-clustering resolved the oversized component
    if all(len(c) <= MAX_COMPONENT_SIZE_BEFORE_SPLIT for c in strict_comps):
        return [list(c) for c in strict_comps if len(c) >= MIN_CLUSTER_SIZE]

    # Pass 2: Fallback to primary entity splitting (source_ip + 20-min time gap)
    split_subgroups: List[List[str]] = []
    ip_groups: Dict[str, List[Alert]] = defaultdict(list)
    for a in comp_alerts_sorted:
        ip_groups[a.source_ip].append(a)

    time_gap = timedelta(minutes=SPLIT_TIME_GAP_MINUTES)
    for ip, ip_alerts in ip_groups.items():
        ip_alerts.sort(key=lambda a: a.timestamp)
        current_subgroup = [ip_alerts[0]]
        for k in range(1, len(ip_alerts)):
            prev_alert = ip_alerts[k - 1]
            curr_alert = ip_alerts[k]
            if (curr_alert.timestamp - prev_alert.timestamp) > time_gap:
                if len(current_subgroup) >= MIN_CLUSTER_SIZE:
                    split_subgroups.append([a.alert_id for a in current_subgroup])
                current_subgroup = [curr_alert]
            else:
                current_subgroup.append(curr_alert)

        if len(current_subgroup) >= MIN_CLUSTER_SIZE:
            split_subgroups.append([a.alert_id for a in current_subgroup])

    return split_subgroups


def cluster_alerts(db: Session, force_recluster: bool = True):
    """Executes the full hybrid clustering pipeline and updates incidents in the database."""
    if force_recluster:
        # Reset existing clustering if re-running
        print("Clearing prior incident assignments for clean re-clustering...")
        db.query(Alert).update({Alert.incident_id: None}, synchronize_session=False)
        db.query(Incident).delete(synchronize_session=False)
        db.commit()

    # 1. Fetch unclustered alerts ordered by timestamp
    alerts = (
        db.query(Alert)
        .filter(Alert.incident_id.is_(None))
        .order_by(Alert.timestamp.asc())
        .all()
    )

    if not alerts:
        print("No unclustered alerts found in database.")
        return

    print(f"Fetched {len(alerts)} alerts for clustering.")

    # 2. Generate embeddings
    print("Generating context embeddings using all-MiniLM-L6-v2...")
    embeddings = generate_embeddings(alerts)
    embeddings_map = {a.alert_id: embeddings[idx] for idx, a in enumerate(alerts)}
    alert_map = {a.alert_id: a for a in alerts}

    # 3. Build initial hybrid similarity graph
    print("Evaluating hybrid correlation graph edges (tightened thresholds)...")
    G = build_similarity_graph(alerts, embeddings_map, strict_mode=False)
    print(f"Graph constructed: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    # 4. Find connected components
    raw_components = list(nx.connected_components(G))
    print(f"Found {len(raw_components)} raw connected components.")

    # 5. Apply hard cap and automatic splitting on components > 25 alerts
    final_clusters: List[List[str]] = []
    oversized_split_count = 0

    for comp in raw_components:
        comp_size = len(comp)
        if comp_size < MIN_CLUSTER_SIZE:
            continue

        if comp_size <= MAX_COMPONENT_SIZE_BEFORE_SPLIT:
            final_clusters.append(list(comp))
        else:
            oversized_split_count += 1
            comp_alerts = [alert_map[aid] for aid in comp]
            split_groups = split_large_component(comp_alerts, embeddings_map)
            final_clusters.extend(split_groups)

    if oversized_split_count > 0:
        print(f"Auto-split {oversized_split_count} oversized components (> {MAX_COMPONENT_SIZE_BEFORE_SPLIT} alerts) to prevent percolation.")

    # 6. Create incidents and persist assignments
    now = datetime.now(timezone.utc)
    new_incidents = []
    alert_to_incident: Dict[str, str] = {}

    size_distribution = {"small (2)": 0, "medium (3-9)": 0, "large (10+)": 0}

    for cluster_alert_ids in final_clusters:
        c_size = len(cluster_alert_ids)
        if c_size == 2:
            size_distribution["small (2)"] += 1
        elif 3 <= c_size <= 9:
            size_distribution["medium (3-9)"] += 1
        else:
            size_distribution["large (10+)"] += 1

        inc_id = str(uuid.uuid4())
        incident = Incident(
            incident_id=inc_id,
            severity_score=0.0,
            severity_rank=0,
            mitre_tag=None,
            created_at=now,
        )
        new_incidents.append(incident)

        for alert_id in cluster_alert_ids:
            alert_to_incident[alert_id] = inc_id

    # Persist incidents to database
    print(f"Persisting {len(new_incidents)} incidents and updating {len(alert_to_incident)} alerts...")
    db.bulk_save_objects(new_incidents)
    db.flush()

    # Bulk update alerts with assigned incident_id
    for alert in alerts:
        if alert.alert_id in alert_to_incident:
            alert.incident_id = alert_to_incident[alert.alert_id]

    db.commit()
    print("Clustering pipeline complete and changes committed to DB.")

    unclustered_count = len(alerts) - len(alert_to_incident)

    # 7. Print Summary
    print("\n================ CLUSTERING SUMMARY ================")
    print(f"Total Incidents Created: {len(new_incidents)}")
    print("Incident Size Distribution:")
    for category, count in size_distribution.items():
        print(f"  - {category}: {count}")
    print(f"Total Alerts Clustered: {len(alert_to_incident)}")
    print(f"Total Isolated Alerts Left Unclustered: {unclustered_count}")

    # 8. Sanity check warning assertion for oversized incidents (> 100 alerts)
    oversized_final = [len(c) for c in final_clusters if len(c) > SANITY_MAX_ALERT_WARNING]
    if oversized_final:
        print(f"\n[WARNING]: Detected {len(oversized_final)} incident(s) with > {SANITY_MAX_ALERT_WARNING} alerts! Sizes: {oversized_final}")
    else:
        print(f"Sanity Check: PASS (No incident exceeded {SANITY_MAX_ALERT_WARNING} alerts).")
    print("====================================================\n")


def sanity_check_ground_truth(db: Session):
    """Verifies that planted attack scenarios A, B, and C were properly clustered."""
    gt_path = backend_dir / "data" / "ground_truth.json"
    if not gt_path.exists():
        print(f"Ground truth file not found at {gt_path}")
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print("================ GROUND TRUTH SANITY CHECK ================")
    for scenario_name, alert_ids in ground_truth.items():
        alerts = db.query(Alert).filter(Alert.alert_id.in_(alert_ids)).all()
        incident_ids = {a.incident_id for a in alerts if a.incident_id is not None}
        unclustered = sum(1 for a in alerts if a.incident_id is None)

        print(f"\n[{scenario_name}]")
        print(f"  - Planted alert count: {len(alert_ids)}")
        print(f"  - Clustered alert count: {len(alert_ids) - unclustered}")
        print(f"  - Unique incident IDs: {len(incident_ids)}")
        if unclustered:
            print(f"  - Unclustered alerts: {unclustered}")

        if len(incident_ids) == 1 and unclustered == 0:
            print("  -> STATUS: PASS (All alerts successfully captured in a single incident)")
        elif len(incident_ids) >= 1 and unclustered == 0:
            print(f"  -> STATUS: ACCEPTABLE (Alerts grouped into {len(incident_ids)} incidents)")
        else:
            print("  -> STATUS: INCOMPLETE (Some alerts remained unclustered)")
    print("===========================================================\n")


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cluster_alerts(db, force_recluster=True)
        sanity_check_ground_truth(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
