# AlertLens Dataset V2 Architectural Design Specification
**Document ID:** DATASET_V2_DESIGN.md  
**Status:** SPECIFICATION & DESIGN REVISION ONLY — AWAITING FORMAL APPROVAL  
**Current State:** 100% FROZEN (2,569 alerts, 490 incidents, 91 actionable, 399 informational, 58 planted alerts, 44/44 tests passing)  
**Target Expansion:** 2,569 &rarr; 3,000 Alerts (+431 Alerts)  
**Classification Guide:** All numerical and behavioral expectations in this document are strictly categorized as **DATASET DESIGN**, **DESIGN TARGET**, **PROJECTED IMPACT (NOT VALIDATED)**, or **OBSERVATIONAL VALIDATION OUTPUT**.

---

## DATASET V2 EXECUTION BOUNDARY

Until explicit approval is provided, this document is specification-only.

**Execution may:**
- Generate new synthetic alerts according to this specification
- Validate schema conformance and foreign-key integrity
- Validate record uniqueness across all tuples
- Run the existing frozen intelligence pipeline
- Calculate empirical V2 metrics
- Produce validation reports comparing actuals against design projections

**Execution may NOT:**
- Modify existing V1 alerts
- Modify existing ground truth (Scenarios A, B, C)
- Modify clustering rules or hyperparameters
- Modify the 3-factor severity ranking formula
- Modify attack progression logic
- Modify correlation confidence logic
- Modify existing MITRE detection mappings
- Modify actionability rules or thresholds
- Tune thresholds to artificially manufacture or improve V2 metrics
- Rewrite tests to accommodate unexpected clustering results

*Any intelligence-layer change requires separate evaluation and explicit approval.*

---

## 1. Exact +431 Alert Allocation Proposal [DATASET DESIGN]

The 431 additional alerts are mathematically apportioned across three distinct functional categories:

```
Total Expansion: +431 Alerts [DATASET DESIGN]
├── Category A: Benign Background Telemetry (+379 alerts, 87.94%)
├── Category B: Correlated Operational Activity (+44 alerts, 10.21%)
│   ├── Sequence B1: Automated Nightly DB Backup & Replication (+22 alerts)
│   └── Sequence B2: Scheduled Configuration Management Rollout (+22 alerts)
└── Category C: Planted Attack Telemetry — Scenario D (+8 alerts, 1.86%)
    └── Multi-Asset Lateral Movement (Foothold → Bastion → Crown Jewel)
```

### Event-Type Preservation Matrix [DATASET DESIGN]
The proposed additions adhere strictly to the empirical proportions of the canonical baseline ($\pm 0.5\%$ tolerance) to prevent synthetic distortion:

| Event Type | Baseline (2,569) | Baseline % | Proposed Additions (+431) | Dataset V2 Total (3,000) | V2 % | Delta % |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `successful_login` | 879 | 34.22% | +148 (130 bg + 14 ops + 4 attack) | 1,027 | 34.23% | +0.01% |
| `failed_login` | 547 | 21.30% | +80 (80 bg + 0 ops + 0 attack) | 627 | 20.90% | -0.40% |
| `file_download` | 388 | 15.10% | +66 (60 bg + 6 ops + 0 attack) | 454 | 15.13% | +0.03% |
| `file_access` | 377 | 14.67% | +79 (55 bg + 20 ops + 4 attack) | 456 | 15.20% | +0.53% |
| `vpn_connect` | 249 | 9.70% | +39 (35 bg + 4 ops + 0 attack) | 288 | 9.60% | -0.10% |
| `password_change` | 122 | 4.75% | +19 (19 bg + 0 ops + 0 attack) | 141 | 4.70% | -0.05% |
| Specialized Attack Events | 7 | 0.27% | +0 | 7 | 0.23% | -0.04% |
| **Total** | **2,569** | **100.00%** | **+431** | **3,000** | **100.00%** | **0.00%** |

---

## 2. Planted Attack Scenario Design: Scenario D [DATASET DESIGN]

### A. Threat Scenario Overview
- **Scenario ID:** `scenario_d_lateral_movement`
- **Threat Actor Narrative:** An adversary holding compromised credentials for senior DevOps engineer `dlee` initiates lateral traversal across multiple internal security zones from an engineering workstation foothold (`10.0.1.25`), leveraging developer jump boxes and CI/CD runners to reach high-value customer records.
- **Coverage Justification:** Resolves the genuine behavioral coverage gap identified during the audit (multi-asset horizontal traversal without initial vertical privilege escalation).

### B. Planted Ground-Truth Data Traversal Path [DATASET DESIGN]
```
[10.0.1.25: Foothold Endpoint (ws-eng-04)]
       │
       ▼ (Step 1: SSH Remote Service)
[dev-sandbox-01 (Low Crit)] ──(Step 2: Read api_keys_draft.txt)
       │
       ▼ (Step 3: SSH Pivot)
[ci-cd-runner-01 (Med Crit)] ──(Step 4: Read pipeline_secret.yaml)
       │
       ▼ (Step 5: SSH Remote Service)
[git-internal-01 (Med Crit)] ──(Step 6: Read schema_dump.sql)
       │
       ▼ (Step 7: Admin Database Session)
[customer-pii-db (High Crit)] ──(Step 8: Query customer_records_2026.csv)
```

### C. Planted Telemetry Event Chain (8 Natural Events) [DATASET DESIGN]
The scenario is designed with exactly **8 natural telemetry events**, spacing consecutive pivot steps 2.5 minutes apart across a 17.5-minute window:

| Step | Timestamp Offset | Event Type | User | Source IP | Target Asset | Asset Crit | Raw Log Message |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | $T_0$ (`14:10:00`) | `successful_login` | `dlee` | `10.0.1.25` | `dev-sandbox-01` | Low | Interactive logon session established for user dlee from 10.0.1.25 on dev-sandbox-01 via SSH |
| **2** | $T_0 + 150s$ (`14:12:30`) | `file_access` | `dlee` | `10.0.1.25` | `dev-sandbox-01` | Low | Read access granted for file api_keys_draft.txt to user dlee from IP 10.0.1.25 on dev-sandbox-01 |
| **3** | $T_0 + 300s$ (`14:15:00`) | `successful_login` | `dlee` | `10.0.1.25` | `ci-cd-runner-01` | Medium | Remote service SSH session opened by user dlee from 10.0.1.25 to ci-cd-runner-01 |
| **4** | $T_0 + 450s$ (`14:17:30`) | `file_access` | `dlee` | `10.0.1.25` | `ci-cd-runner-01` | Medium | User dlee accessed file pipeline_secret.yaml on asset ci-cd-runner-01 from 10.0.1.25 |
| **5** | $T_0 + 600s$ (`14:20:00`) | `successful_login` | `dlee` | `10.0.1.25` | `git-internal-01` | Medium | User dlee logged in successfully from 10.0.1.25 to git-internal-01 via Kerberos/SSH |
| **6** | $T_0 + 750s$ (`14:22:30`) | `file_access` | `dlee` | `10.0.1.25` | `git-internal-01` | Medium | Shared storage access: dlee opened schema_dump.sql on network asset git-internal-01 |
| **7** | $T_0 + 900s$ (`14:25:00`) | `successful_login` | `dlee` | `10.0.1.25` | `customer-pii-db` | **High** | Session initiated: user dlee verified from source 10.0.1.25 on crown-jewel customer-pii-db |
| **8** | $T_0 + 1050s$ (`14:27:30`) | `file_access` | `dlee` | `10.0.1.25` | `customer-pii-db` | **High** | User dlee accessed database export customer_records_2026.csv on asset customer-pii-db from 10.0.1.25 |

---

## 3. Correlation Expectations & Intelligence Pipeline Alignment

### A. Graph Topology Expectation [DESIGN TARGET]
- In the frozen pipeline (`backend/ml/clustering.py`), rule edges form when `(same_ip or same_user) and time_diff <= 15 min`.
- In Scenario D, all 8 alerts share `username == "dlee"` and `source_ip == "10.0.1.25"`, with adjacent steps spaced 2.5 minutes apart ($150\text{s} \le 900\text{s}$).
- **Expectation:** The 8 alerts are expected to coalesce into a cohesive connected component. Whether they form an exclusive 8-alert cluster or absorb background activity will be strictly determined during observational validation.

### B. Severity Score Formulation [DESIGN TARGET]
Under the frozen 3-factor ranking formula:
$$\text{Severity Score} = (\text{Asset Criticality} \times 3) + (\text{Event Severity} \times 2) + \ln(\text{Alert Count} + 1)$$
- Top Asset: `customer-pii-db` (High = 3) &rarr; Component = $9.00$.
- Top Event: `successful_login` / `file_access` (Raw = 2) &rarr; Component = $4.00$.
- Alert Volume: 8 alerts &rarr; Component = $\ln(9) \approx 2.20$.
- **Design Target Severity:** **$15.20$** (Subject to the actual constituent alert count formed by clustering).

### C. MITRE ATT&CK Mapping Status [CRITICAL DISTINCTION]
- **Scenario D Design Intent:** Scenario D is designed to represent lateral movement / remote-services behavior.
- **T1021 Status:** T1021 is the proposed MITRE ATT&CK interpretation for this scenario, but the frozen V1 intelligence pipeline does not currently establish T1021 as a validated mapping rule. The actual MITRE result must be determined during validation.
- **Policy Statement:** Adding or modifying a T1021 detection rule would constitute an intelligence-pipeline change and is **OUT OF SCOPE** for this dataset-only V2 execution unless separately approved.

### D. Actionability Triage [OBSERVATIONAL VALIDATION OUTPUT]
- An incident is classified as Actionable if `mitre_tag IS NOT NULL` OR `severity_score >= P90`.
- The actual actionability tier of Scenario D will be recorded as an observational validation output based on the frozen pipeline's empirical scoring and MITRE tagging.

### E. Attack Progression Context [OBSERVATIONAL VALIDATION OUTPUT]
- The progression label for Scenario D will be whatever the frozen Attack Progression logic deterministically produces. No progression logic will be modified specifically for Scenario D.
- If the resulting output is `"None (Isolated Activity)"`, that will be recorded as an observed validation result.
- If it produces another existing label, the actual result will be recorded without inventing new labels.

### F. Correlation Confidence Context [DESIGN TARGET & OBSERVATIONAL OUTPUT]
- Scenario D is expected to form a cohesive multi-alert component because of the strong temporal, username, source-IP, and multi-asset relationships.
- The exact correlation confidence value **MUST be produced by the existing frozen algorithm during validation**.
- The 85% value represents an illustrative **DESIGN TARGET** based on theoretical entity overlap, never a guaranteed output.
- The confidence algorithm will not be modified to force an 85% result.

---

## 4. Correlated Operational Sequences (Category B: +44 Alerts) [DATASET DESIGN]

To reflect enterprise reality where multi-event administrative scripts run routinely without being malicious, two non-attack operational sequences are incorporated:

### Sequence B1: Automated Nightly Database Backup & Storage Sync (22 Alerts) [DATASET DESIGN]
- **Service Account:** `svc_backup` (source IP: `10.0.4.15`)
- **Execution Window:** Nightly at `02:00:00` &rarr; `02:35:00` UTC
- **Workflow:** Automated cron job authenticating, snapshotting, and archiving databases across `pki-root-ca`, `finance-db-01`, `customer-pii-db`, and `backup-archive-cold`.
- **Target Category:** Benign administrative operational batch.

### Sequence B2: Scheduled Configuration Management Rollout (22 Alerts) [DATASET DESIGN]
- **Service Account:** `svc_deploy` (source IP: `10.0.10.12`)
- **Execution Window:** Nightly at `04:00:00` &rarr; `04:28:00` UTC
- **Workflow:** Automated deployment verification traversing `dev-sandbox-01`, `dev-sandbox-02`, and `ci-cd-runner-01`.
- **Target Category:** Benign IT maintenance batch.

---

## 5. PROJECTED IMPACT — NOT YET VALIDATED

> [!IMPORTANT]
> The numbers below are design-stage estimates and mathematical projections. They are **NOT guaranteed outcomes**. They will be replaced by empirically measured V2 results after the frozen pipeline executes against the generated dataset. The system will NOT be tuned or altered to force these values.

| Dimension / Metric | Dataset V1 (Current Frozen Baseline) | Dataset V2 (Design Projection — NOT VALIDATED) | Methodological Nature |
| :--- | :--- | :--- | :--- |
| **Total Telemetry Alerts** | **2,569** | **3,000** | Exact generation target (+431 alerts) |
| **Total Correlated Clusters** | **490** | **~565 – 575** | Projection based on ~33% singleton rate in background noise |
| **Actionable Incidents** | **91** | **~98 – 102** | Projection based on high-criticality asset distribution |
| **Informational Clusters** | **399** | **~467 – 473** | Projection based on routine operational batches |
| **90th Percentile Severity ($P_{90}$)** | **16.61** | **16.61 – 16.75** | Projection based on scale-invariant severity distributions |
| **Planted Ground-Truth Scenarios** | **3** (A, B, C) | **4** (A, B, C, D) | Exact planned benchmark expansion |
| **Planted Ground-Truth Alerts** | **58** | **66** (+8 alerts) | Exact planned ground-truth alert count |
| **Aggregate Mean Recall** | **100.0%** | **100.0% (Target)** | Strict protected invariant |
| **Aggregate Mean Precision** | **78.6%** | **83.9% (Projection)** | Mathematical projection based on adding a clean Scenario D |
| **Estimated Triage Time Saved** | **92.9%** | **~93.2%** | Illustrative model projection |

### Clarification on Projected Precision
The projected aggregate precision of **83.9%** is a mathematical design calculation:
$$\text{Projected Precision} = \frac{1.0\ (\text{Scen A}) + 0.50\ (\text{Scen B}) + 0.8571\ (\text{Scen C}) + 1.0\ (\text{Projected Scen D})}{4} = \frac{3.3571}{4} = 83.93\%$$
This projection assumes that Scenario D clusters cleanly without absorbing background noise. The actual V2 precision will depend entirely on the clustering output produced by the frozen pipeline. The dataset will not be optimized or manipulated specifically to manufacture a higher precision figure.

---

## 6. Observational Validation Gates

Execution must follow a strict 6-gate validation protocol. All validation gates are **strictly observational**—they record empirical outcomes and must not be satisfied by modifying the intelligence pipeline to force expected outputs.

```
Validation Protocol:
[Gate 1: Data Integrity]       — Verify exactly 3,000 records, zero 5-tuple duplicates, valid foreign keys
[Gate 2: Frozen Clustering]    — Execute frozen clustering; observe actual Scenario D cluster formation
[Gate 3: Frozen MITRE Tagging] — Execute frozen MITRE logic; record actual tag (no rule injection)
[Gate 4: Frozen Actionability] — Execute frozen scoring & tiering; record actual classification
[Gate 5: Empirical Benchmark]  — Calculate actual TP, FP, FN, precision, and recall across all 4 scenarios
[Gate 6: Regression Invariant] — Execute full automated test suite; verify zero operational regressions
```

### Detailed Gate Specifications

#### Gate 1: Generation & Data Integrity
- Total records in PostgreSQL: exactly `3,000`.
- Baseline alerts preserved: exactly `2,569`.
- Added alerts: exactly `431`.
- Deduplication check: zero duplicates across `(timestamp, source_ip, username, event_type, target_asset)`.
- Foreign key integrity: all `incident_id` values reference valid primary keys.

#### Gate 2: Frozen Clustering Execution
- Run `backend/ml/clustering.py` using the frozen hyperparameters.
- Observe:
  - Total clusters produced.
  - Dominant incident ID capturing Scenario D planted alert IDs.
  - Actual alert count in Scenario D's dominant incident.
  - Any background alerts grouped into Scenario D.

#### Gate 3: Frozen MITRE ATT&CK Evaluation
- Run `backend/ml/ranking.py` using existing frozen rules.
- Record the actual assigned MITRE tag for Scenario D.
- Do NOT inject or modify detection rules to force a `T1021` tag.

#### Gate 4: Actionability Triage Audit
- Record the empirical Severity Score of Scenario D.
- Record whether Scenario D is classified as `actionable` or `informational`.
- Measure the empirical $P_{90}$ threshold across all clusters.

#### Gate 5: Ground-Truth Evaluation
- Execute `backend/ml/metrics.py` against the extended 4-scenario `ground_truth.json`.
- Compute and report measured values:
  - Scenario A: actual precision & recall
  - Scenario B: actual precision & recall
  - Scenario C: actual precision & recall
  - Scenario D: actual TP, FP, FN, precision, and recall
  - Aggregate Mean Recall (must equal `1.0` to satisfy recall protection)
  - Aggregate Mean Precision (measured empirical outcome)

#### Gate 6: Full Regression Verification
- Run complete test suite (`pytest tests/ -v`).
- Confirm that existing operational capabilities, security controls, and endpoint contracts remain 100% functional.

---

## 7. Assumptions & Governance

1. **Synthetic Data Realism:** All 431 generated alerts use realistic enterprise values from existing pools (`USERNAMES`, `ASSETS`, `INTERNAL_IPS`, `FILENAMES`).
2. **Timeline Fitting:** New background and operational alerts are distributed across the existing 51-hour operational timeline (`2026-09-21` to `2026-09-23`) to prevent artificial chronological gaps.
3. **Immutability of Frozen Pipeline:** All clustering, embedding, scoring, progression, confidence, and MITRE code remains completely untouched.
4. **Separation of Roles:** This specification represents a design and planning deliverable. Database generation and benchmark execution require separate, explicit confirmation.
