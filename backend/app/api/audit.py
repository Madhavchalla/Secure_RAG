from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.audit import AuditLog, SecurityEvent, RiskAssessment
from app.schemas.audit import AuditLogResponse, SecurityEventResponse, RiskAssessmentResponse
from app.api.deps import require_admin

router = APIRouter(prefix="/audit", tags=["Audits & Security Events"])


@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve system audit logs for administrative inspection.
    """
    query = db.query(AuditLog)
    if status_filter:
        query = query.filter(AuditLog.status == status_filter.upper())
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    # Enrich with username
    results = []
    for log in logs:
        res = AuditLogResponse.model_validate(log)
        if log.user:
            res.username = log.user.username
        results.append(res)
    return results


@router.get("/security-events", response_model=List[SecurityEventResponse])
def get_security_events(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve high-severity security incidents (prompt injections, quarantine triggers).
    """
    query = db.query(SecurityEvent)
    if severity:
        query = query.filter(SecurityEvent.severity == severity.upper())

    events = query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()

    results = []
    for ev in events:
        res = SecurityEventResponse.model_validate(ev)
        if ev.user:
            res.username = ev.user.username
        results.append(res)
    return results


@router.get("/risk-assessments", response_model=List[RiskAssessmentResponse])
def get_risk_assessments(
    limit: int = Query(50, ge=1, le=200),
    decision: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve detailed risk assessments and explainability telemetry.
    """
    query = db.query(RiskAssessment)
    if decision:
        query = query.filter(RiskAssessment.decision == decision.upper())

    assessments = query.order_by(RiskAssessment.created_at.desc()).limit(limit).all()

    results = []
    for r in assessments:
        res = RiskAssessmentResponse.model_validate(r)
        if r.user:
            res.username = r.user.username
        results.append(res)
    return results
