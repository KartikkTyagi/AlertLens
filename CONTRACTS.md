# AlertLens — Shared Contracts

## Database Schema

### alerts table
- alert_id (string, primary key, UUID)
- timestamp (datetime)
- source_ip (string)
- username (string)
- event_type (string) — e.g. failed_login, file_download, privilege_escalation
- target_asset (string)
- asset_criticality (string) — one of: low, medium, high
- raw_message (text) — free-text description, used for embeddings later
- incident_id (string, nullable, foreign key) — filled in once clustering runs

### incidents table
- incident_id (string, primary key, UUID)
- severity_score (float)
- severity_rank (integer)
- mitre_tag (string, nullable) — e.g. "T1110"
- created_at (datetime)
- acknowledged (boolean, default false) — new in Phase 9
- acknowledged_by (string, nullable) — username, new in Phase 9
- acknowledged_at (datetime, nullable) — new in Phase 9
- confidence_tier (string) — one of: "actionable", "informational"
- score_asset_component (float) — weighted asset criticality score
- score_event_component (float) — weighted event severity score
- score_volume_component (float) — log-scaled volume score
- top_asset_factor (string, nullable) — e.g. "finance-db-01 (high criticality)"
- top_event_factor (string, nullable) — e.g. "privilege_escalation (severity 5)"
- asset_raw_level (string, nullable) — e.g. "HIGH"
- asset_raw_score (integer) — e.g. 3
- event_type_used (string, nullable) — e.g. "privilege_escalation"
- event_raw_score (integer) — e.g. 5
- alert_count_used (integer) — e.g. 7

### incident_briefs table
- brief_id (string, primary key, UUID)
- incident_id (string, foreign key -> incidents.incident_id)
- summary_text (text)
- source_alert_ids (JSON array of strings) — for traceability
- created_at (datetime)

### audit_log table
- log_id (string, primary key, UUID)
- action (string) — e.g. "viewed_brief", "acknowledged_incident"
- incident_id (string, nullable)
- timestamp (datetime)
- user_id (string, nullable)

### users table (new in Phase 9)
- user_id (string, primary key, UUID)
- username (string, unique)
- hashed_password (string)
- role (string) — one of: analyst, admin

---

## API Response Shapes

### POST /auth/login
Request:
```json
{
  "username": "analyst_demo",
  "password": "demo1234"
}
```
Returns:
```json
{
  "access_token": "...",
  "token_type": "bearer",
  "role": "analyst",
  "username": "analyst_demo"
}
```

### GET /incidents
Optional query parameter: `tier` (`actionable` | `informational` | `all`, default: `actionable`)
Returns a JSON array of:
```json
{
  "incident_id": "string",
  "severity_score": 0.0,
  "severity_rank": 1,
  "mitre_tag": "T1110",
  "alert_count": 12,
  "created_at": "ISO8601 datetime",
  "acknowledged": false,
  "acknowledged_by": null,
  "acknowledged_at": null,
  "confidence_tier": "actionable",
  "score_breakdown": {
    "asset_component": 9.0,
    "event_component": 10.0,
    "volume_component": 2.08,
    "top_asset_factor": "finance-db-01 (high criticality)",
    "top_event_factor": "privilege_escalation (severity 5)",
    "asset_raw_level": "HIGH",
    "asset_raw_score": 3,
    "event_type_used": "privilege_escalation",
    "event_raw_score": 5,
    "alert_count_used": 7
  }
}
```

### GET /incidents/{id}/brief
Returns:
```json
{
  "incident_id": "string",
  "summary_text": "string",
  "source_alert_ids": ["string", "..."],
  "mitre_tag": "T1110"
}
```

### POST /incidents/{id}/acknowledge
Returns updated incident:
```json
{
  "incident_id": "string",
  "acknowledged": true,
  "acknowledged_by": "analyst_demo",
  "acknowledged_at": "ISO8601 datetime"
}
```

### GET /audit-log
Returns a JSON array of:
```json
{
  "log_id": "string",
  "action": "viewed_brief",
  "incident_id": "string",
  "timestamp": "ISO8601 datetime",
  "user_id": "analyst_demo"
}
```
