import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Load environment variables
load_dotenv(backend_dir / ".env")
load_dotenv(backend_dir / ".env.example")

from app.database import Base, SessionLocal, engine
from app.models import Alert, Incident, IncidentBrief

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Constants
MAX_PROMPT_ALERTS = 15
DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
CANDIDATE_GROQ_MODELS = [
    GROQ_MODEL,
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
FALLBACK_SUMMARY = "[AI summary unavailable — see raw alerts below for details]"


def build_summarization_prompt(
    incident: Incident,
    alerts: List[Alert],
) -> Tuple[str, List[str]]:
    """Constructs a structured prompt for the LLM and records source alert IDs for traceability.
    
    Caps representative alerts to at most MAX_PROMPT_ALERTS (15) to keep prompt size manageable.
    Returns (prompt_text, source_alert_ids).
    """
    # Select representative alerts: first few, middle, and last to capture full progression
    if len(alerts) <= MAX_PROMPT_ALERTS:
        sampled_alerts = alerts
    else:
        step = len(alerts) / MAX_PROMPT_ALERTS
        indices = [int(i * step) for i in range(MAX_PROMPT_ALERTS)]
        sampled_alerts = [alerts[idx] for idx in indices]

    source_alert_ids = [a.alert_id for a in sampled_alerts]

    # Format alerts for prompt
    alert_lines = []
    for idx, a in enumerate(sampled_alerts, start=1):
        ts_str = a.timestamp.strftime("%Y-%m-%d %H:%M:%S") if a.timestamp else "N/A"
        line = (
            f"- Alert #{idx} [{ts_str}] Event: {a.event_type} | User: {a.username} | "
            f"Asset: {a.target_asset} ({a.asset_criticality}) | IP: {a.source_ip} | Message: {a.raw_message}"
        )
        alert_lines.append(line)

    alerts_block = "\n".join(alert_lines)

    prompt = f"""You are an elite Security Operations Center (SOC) Tier-3 Incident Responder.
Analyze the following security incident and write a concise, authoritative, human-readable brief for an analyst.

INCIDENT CONTEXT:
- Severity Score: {incident.severity_score}
- Severity Rank: #{incident.severity_rank}
- MITRE ATT&CK Tag: {incident.mitre_tag or "Untagged"}
- Total Alert Count: {len(alerts)}
- Sampled Alerts ({len(sampled_alerts)} shown below):

{alerts_block}

INSTRUCTIONS:
Produce a plain-English response structured with EXACTLY these three headings:

### What Happened
(2-3 plain-English sentences summarizing the specific attack pattern or operational anomaly observed across the alerts.)

### Why It Matters
(1-2 sentences explaining why this incident is significant, referencing the targeted asset criticality, blast radius, or MITRE technique if applicable.)

### Recommended Next Step
(1 concrete, actionable suggestion for the SOC analyst to contain, investigate, or remediate the issue.)

Do NOT include pleasantries, disclaimers, or extra introductory text. Begin directly with "### What Happened"."""
    return prompt, source_alert_ids


def call_groq_api(prompt: str) -> str:
    """Calls Groq API using groq Python SDK with model fallback."""
    from groq import Groq, NotFoundError

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("your_groq_api_key"):
        raise ValueError("GROQ_API_KEY environment variable is not configured with a valid key.")

    client = Groq(api_key=api_key, timeout=15.0)
    
    last_err = None
    # Deduplicate candidates while preserving order
    models_to_try = list(dict.fromkeys(CANDIDATE_GROQ_MODELS))
    for model_name in models_to_try:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional cybersecurity incident response analyst. You generate accurate, structured triage briefs.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                model=model_name,
                temperature=0.2,
                max_tokens=500,
            )
            content = chat_completion.choices[0].message.content
            return content.strip() if content else FALLBACK_SUMMARY
        except NotFoundError as nfe:
            last_err = nfe
            continue
        except Exception:
            raise

    if last_err:
        raise last_err
    return FALLBACK_SUMMARY


def call_ollama_api(prompt: str) -> str:
    """Calls local Ollama API instance (stub / optional fallback)."""
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama3.1",
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip() or FALLBACK_SUMMARY


def generate_summary(incident: Incident, alerts: List[Alert]) -> Tuple[str, List[str]]:
    """Generates an AI incident brief with graceful fallback in case of errors.
    
    Returns (summary_text, source_alert_ids).
    """
    if not alerts:
        return "[No source alerts found for this incident]", []

    prompt, source_alert_ids = build_summarization_prompt(incident, alerts)
    provider = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).lower()

    try:
        if provider == "groq":
            summary = call_groq_api(prompt)
        elif provider == "ollama":
            summary = call_ollama_api(prompt)
        else:
            logger.warning("Unknown LLM_PROVIDER '%s', falling back to Groq.", provider)
            summary = call_groq_api(prompt)
        return summary, source_alert_ids
    except Exception as e:
        logger.warning(
            "AI generation failed for incident %s (%s: %s). Using fallback summary.",
            incident.incident_id,
            type(e).__name__,
            e,
        )
        return FALLBACK_SUMMARY, source_alert_ids


def summarize_incidents(
    db: Session,
    force_update: bool = False,
    delay_seconds: float = 1.5,
    limit: Optional[int] = None,
):
    """Iterates through incidents lacking a brief, generates summaries, and stores them in DB."""
    # Find incidents
    query = db.query(Incident).order_by(Incident.severity_rank.asc())
    if not force_update:
        # Exclude incidents that already have a non-empty brief
        existing_brief_inc_ids = {
            b.incident_id for b in db.query(IncidentBrief.incident_id).all()
        }
        all_incidents = [inc for inc in query.all() if inc.incident_id not in existing_brief_inc_ids]
    else:
        all_incidents = query.all()

    if limit:
        all_incidents = all_incidents[:limit]

    total = len(all_incidents)
    if total == 0:
        print("All incidents already have briefs generated. Use --force to regenerate.")
        return

    print(f"\n================ AI INCIDENT SUMMARIZATION ================")
    print(f"Provider: {os.getenv('LLM_PROVIDER', DEFAULT_LLM_PROVIDER)} | Model: {GROQ_MODEL}")
    print(f"Generating briefs for {total} incident(s) with {delay_seconds}s rate-limit delay...")
    print("===========================================================\n")

    successful = 0
    fallback_count = 0

    for idx, inc in enumerate(all_incidents, start=1):
        alerts = (
            db.query(Alert)
            .filter(Alert.incident_id == inc.incident_id)
            .order_by(Alert.timestamp.asc())
            .all()
        )

        print(f"[{idx}/{total}] Summarizing Incident #{inc.severity_rank} ({inc.incident_id[:8]}...) [{len(alerts)} alerts]...", end=" ", flush=True)

        summary_text, source_ids = generate_summary(inc, alerts)

        # Check existing brief record
        brief = db.query(IncidentBrief).filter(IncidentBrief.incident_id == inc.incident_id).first()
        if not brief:
            brief = IncidentBrief(
                brief_id=str(uuid.uuid4()),
                incident_id=inc.incident_id,
                summary_text=summary_text,
                source_alert_ids=source_ids,
                created_at=datetime.now(timezone.utc),
            )
            db.add(brief)
        else:
            brief.summary_text = summary_text
            brief.source_alert_ids = source_ids
            brief.created_at = datetime.now(timezone.utc)

        db.commit()

        if summary_text == FALLBACK_SUMMARY:
            fallback_count += 1
            print("FALLBACK RECORDED")
        else:
            successful += 1
            print("DONE")

        # Rate-limiting sleep between calls
        if idx < total:
            time.sleep(delay_seconds)

    print("\n================ SUMMARIZATION COMPLETE ================")
    print(f"Total Processed: {total}")
    print(f"AI Briefs Generated: {successful}")
    print(f"Fallback Briefs Recorded: {fallback_count}")
    print("========================================================\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate AI Incident Briefs for AlertLens")
    parser.add_argument("--force", action="store_true", help="Force regenerate existing briefs")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of incidents to summarize")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay in seconds between API calls")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        summarize_incidents(
            db,
            force_update=args.force,
            delay_seconds=args.delay,
            limit=args.limit,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
