"""
AlertLens — Idempotent AI Brief Backfill
Generates authentic Groq AI incident briefs for all actionable incidents
and any incidents lacking persisted briefs.
"""

import os
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models import Incident, Alert, IncidentBrief
from ml.summarize import generate_summary, FALLBACK_SUMMARY
from datetime import datetime, timezone
import uuid

def backfill():
    db = SessionLocal()
    try:
        # Find all actionable incidents that either have NO brief or have FALLBACK_SUMMARY
        incidents = (
            db.query(Incident)
            .filter(Incident.confidence_tier == "actionable")
            .order_by(Incident.severity_rank.asc())
            .all()
        )

        targets = []
        for inc in incidents:
            brief = db.query(IncidentBrief).filter(IncidentBrief.incident_id == inc.incident_id).first()
            if not brief or not brief.summary_text or FALLBACK_SUMMARY in brief.summary_text:
                targets.append(inc)

        # Also find any other incident lacking a brief entirely
        all_missing = (
            db.query(Incident)
            .outerjoin(IncidentBrief, Incident.incident_id == IncidentBrief.incident_id)
            .filter(IncidentBrief.brief_id.is_(None))
            .all()
        )
        for inc in all_missing:
            if inc not in targets:
                targets.append(inc)

        print(f"Found {len(targets)} incident(s) needing authentic AI briefs.")
        if not targets:
            print("All actionable and existing incidents already have authentic AI briefs.")
            return

        success_count = 0
        for idx, inc in enumerate(targets, start=1):
            alerts = (
                db.query(Alert)
                .filter(Alert.incident_id == inc.incident_id)
                .order_by(Alert.timestamp.asc())
                .all()
            )
            print(f"[{idx}/{len(targets)}] Generating AI brief for Incident #{inc.severity_rank} ({inc.incident_id[:8]}...) [{len(alerts)} alerts]...", end=" ", flush=True)

            summary_text, source_ids = generate_summary(inc, alerts)
            if summary_text and summary_text != FALLBACK_SUMMARY:
                brief = db.query(IncidentBrief).filter(IncidentBrief.incident_id == inc.incident_id).first()
                now = datetime.now(timezone.utc)
                if not brief:
                    brief = IncidentBrief(
                        brief_id=str(uuid.uuid4()),
                        incident_id=inc.incident_id,
                        summary_text=summary_text,
                        source_alert_ids=source_ids,
                        created_at=now,
                    )
                    db.add(brief)
                else:
                    brief.summary_text = summary_text
                    brief.source_alert_ids = source_ids
                    brief.created_at = now
                db.commit()
                success_count += 1
                print("DONE")
            else:
                print("SKIPPED (Fallback returned)")

            # Sleep 1.5s between Groq calls to respect rate limits
            if idx < len(targets):
                time.sleep(1.5)

        print(f"\nBackfill complete: Successfully updated {success_count}/{len(targets)} briefs with authentic Groq analysis.")
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
