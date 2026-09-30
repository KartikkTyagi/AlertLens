import os
import asyncio
from contextlib import asynccontextmanager
import logging
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

import asyncpg

from .database import Base, engine, SessionLocal, DATABASE_URL
from . import models  # noqa: F401 - ensure models are registered with Base.metadata
from .models import Incident, Alert, User
from .schemas import IncidentOut, ScoreBreakdownOut
from .routers import alerts, incidents, metrics, websocket, auth, audit
from .websocket_manager import manager
from .auth import get_password_hash

logger = logging.getLogger("uvicorn.error")


def migrate_incident_columns():
    """Idempotently adds Phase 9 acknowledgment columns to incidents table if not present."""
    if not DATABASE_URL.startswith("postgresql"):
        return

    logger.info("Verifying schema columns for incidents table (Phase 9)...")
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(
                        """
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS acknowledged BOOLEAN DEFAULT FALSE;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS acknowledged_by VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP WITH TIME ZONE;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS confidence_tier VARCHAR DEFAULT 'actionable';
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS attack_progression VARCHAR DEFAULT 'None (Isolated Activity)';
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS progression_detail VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS correlation_confidence FLOAT DEFAULT 0.75;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS confidence_reason VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS score_asset_component FLOAT DEFAULT 0.0;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS score_event_component FLOAT DEFAULT 0.0;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS score_volume_component FLOAT DEFAULT 0.0;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS top_asset_factor VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS top_event_factor VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS asset_raw_level VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS asset_raw_score INTEGER DEFAULT 1;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS event_type_used VARCHAR;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS event_raw_score INTEGER DEFAULT 1;
                        ALTER TABLE incidents ADD COLUMN IF NOT EXISTS alert_count_used INTEGER DEFAULT 0;

                        CREATE INDEX IF NOT EXISTS ix_alerts_incident_id ON alerts(incident_id);
                        CREATE INDEX IF NOT EXISTS ix_incidents_severity_rank ON incidents(severity_rank);
                        """
                    )
                )
        logger.info("Incidents table columns and indexes verified/migrated.")
    except Exception as e:
        logger.error("Failed to migrate incident columns: %s", e)


ENABLE_DEMO_USERS = os.getenv("ENABLE_DEMO_USERS", "true").lower() in ("true", "1", "yes")


def seed_demo_users():
    """Seeds analyst_demo and admin_demo users when ENABLE_DEMO_USERS is active."""
    if not ENABLE_DEMO_USERS:
        logger.info("Demo users disabled via ENABLE_DEMO_USERS=false configuration.")
        return

    db = SessionLocal()
    try:
        demo_accounts = [
            ("analyst_demo", "demo1234", "analyst"),
            ("admin_demo", "admin1234", "admin"),
        ]

        for username, password, role in demo_accounts:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                new_user = User(
                    user_id=str(uuid.uuid4()),
                    username=username,
                    hashed_password=get_password_hash(password),
                    role=role,
                )
                db.add(new_user)
                db.commit()
                logger.info("Created demo user '%s' (%s).", username, role)

        # Log demo credentials status safely without printing plaintext passwords
        logger.info("=" * 70)
        logger.info("AlertLens Demo Accounts Enabled (ENABLE_DEMO_USERS=true):")
        logger.info("  Analyst:  username: analyst_demo | role: analyst")
        logger.info("  Admin:    username: admin_demo   | role: admin")
        logger.info("  [SECURITY NOTICE]: Set ENABLE_DEMO_USERS=false for production.")
        logger.info("=" * 70)
    except Exception as e:
        logger.error("Failed to seed demo users: %s", e)
    finally:
        db.close()


def init_db_trigger():
    """Sets up an idempotent Postgres trigger for NOTIFY on new incident inserts."""
    if not DATABASE_URL.startswith("postgresql"):
        logger.info("Non-Postgres database detected, skipping LISTEN/NOTIFY trigger setup.")
        return

    logger.info("Configuring Postgres trigger for LISTEN/NOTIFY on 'incidents'...")
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(
                        """
                        CREATE OR REPLACE FUNCTION notify_new_incident() RETURNS TRIGGER AS $$
                        BEGIN
                            PERFORM pg_notify('new_incident', NEW.incident_id::text);
                            RETURN NEW;
                        END;
                        $$ LANGUAGE plpgsql;

                        DROP TRIGGER IF EXISTS trg_new_incident ON incidents;
                        CREATE TRIGGER trg_new_incident
                        AFTER INSERT ON incidents
                        FOR EACH ROW EXECUTE FUNCTION notify_new_incident();
                        """
                    )
                )
        logger.info("Postgres trigger trg_new_incident created successfully.")
    except Exception as e:
        logger.error("Failed to initialize Postgres trigger: %s", e)


def fetch_incident_payload(incident_id: str):
    """Synchronously queries the full incident details and calculates alert count."""
    db = SessionLocal()
    try:
        inc = db.query(Incident).filter(Incident.incident_id == incident_id).first()
        if not inc:
            return None
        alert_count = db.query(Alert).filter(Alert.incident_id == incident_id).count()
        from .routers.incidents import make_incident_out
        incident_out = make_incident_out(inc, alert_count)
        return incident_out.model_dump(mode="json")
    finally:
        db.close()


async def listen_pg_notifications():
    """Asynchronous background task listening for 'new_incident' Postgres notifications."""
    if not DATABASE_URL.startswith("postgresql"):
        return

    asyncpg_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    while True:
        conn = None
        try:
            logger.info("Connecting to Postgres via asyncpg for LISTEN/NOTIFY...")
            conn = await asyncpg.connect(asyncpg_url)
            logger.info("asyncpg connection established. Listening on channel 'new_incident'...")

            async def on_new_incident(connection, pid, channel, payload):
                incident_id = payload
                logger.info("Postgres NOTIFY received: new_incident payload=%s", incident_id)
                try:
                    payload_dict = await asyncio.to_thread(fetch_incident_payload, incident_id)
                    if payload_dict:
                        logger.info("Broadcasting new incident %s to WebSocket clients", incident_id)
                        await manager.broadcast(payload_dict)
                    else:
                        logger.warning("Incident %s not found in DB for broadcast", incident_id)
                except Exception as ex:
                    logger.error("Error during incident broadcast: %s", ex)

            await conn.add_listener("new_incident", on_new_incident)

            # Keep task alive
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Postgres listener background task cancelled.")
            if conn and not conn.is_closed():
                await conn.close()
            break
        except Exception as e:
            logger.warning("asyncpg listener error: %s. Reconnecting in 3s...", e)
            if conn and not conn.is_closed():
                try:
                    await conn.close()
                except Exception:
                    pass
            await asyncio.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup if they don't exist
    Base.metadata.create_all(bind=engine)
    migrate_incident_columns()
    seed_demo_users()
    init_db_trigger()

    listener_task = asyncio.create_task(listen_pg_notifications())
    try:
        yield
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="AlertLens API",
    description="AI-powered SOC alert triage backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend dashboard (restricted origins, explicit methods/headers)
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent"],
)


# Global unhandled exception handler for clean error responses (no stack trace or internal error leakage)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    logger.error("Unhandled server exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact your SOC administrator."},
    )


# Include routers
app.include_router(auth.router)
app.include_router(alerts.router)
app.include_router(incidents.router)
app.include_router(metrics.router)
app.include_router(websocket.router)
app.include_router(audit.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "alertlens-backend"}
