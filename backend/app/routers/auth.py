from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, AuditLog
from ..schemas import LoginRequest, TokenResponse, UserOut
from ..auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token."""
    user = db.query(User).filter(User.username == login_req.username).first()
    if not user or not verify_password(login_req.password, user.hashed_password):
        # Security Audit Log: track failed authentication attempt (never log raw password)
        fail_audit = AuditLog(
            log_id=str(uuid.uuid4()),
            action="LOGIN_FAILURE",
            incident_id=None,
            user_id=login_req.username[:64] if login_req.username else "anonymous",
            timestamp=datetime.now(timezone.utc),
        )
        db.add(fail_audit)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Security Audit Log: track successful authentication
    success_audit = AuditLog(
        log_id=str(uuid.uuid4()),
        action="LOGIN_SUCCESS",
        incident_id=None,
        user_id=user.username,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(success_audit)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.user_id}
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve profile of currently authenticated user."""
    return current_user
