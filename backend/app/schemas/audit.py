from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    details_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SecurityEventResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    event_type: str
    severity: str
    description: str
    metadata_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RiskAssessmentResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str] = None
    query_text: str
    query_risk_score: float
    session_risk_score: float
    doc_sensitivity_score: float
    final_risk_score: float
    decision: str
    reasons: str
    created_at: datetime

    class Config:
        from_attributes = True
