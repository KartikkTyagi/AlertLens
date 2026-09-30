from datetime import datetime, timezone
from typing import List
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AuditLog, User
from ..schemas import AuditLogOut
from ..auth import require_admin

router = APIRouter(prefix="/audit-log", tags=["Audit Log"])


@router.get("", response_model=List[AuditLogOut])
def get_audit_log(
    limit: int = Query(100, ge=1, le=1000, description="Max audit entries to retrieve"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    """Retrieve audit log entries, ordered by timestamp descending. Requires Admin role."""
    # Security Audit Log: record admin inspection of security audit trail
    inspect_audit = AuditLog(
        log_id=str(uuid.uuid4()),
        action="AUDIT_LOG_ACCESSED",
        incident_id=None,
        user_id=admin_user.username,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(inspect_audit)
    db.commit()

    entries = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc(), AuditLog.log_id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entries
