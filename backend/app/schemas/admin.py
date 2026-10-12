from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AdminDashboardMetrics(BaseModel):
    total_documents: int
    active_documents: int
    quarantined_documents: int
    total_users: int
    total_queries: int
    blocked_queries: int
    restricted_queries: int
    security_incidents: int
    risk_distribution: Dict[str, int]  # {'ALLOW': count, 'RESTRICT': count, 'VERIFY': count, 'BLOCK': count}


class QuarantineReviewAction(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT)$")
    sensitivity_level: Optional[str] = Field("LOW", pattern="^(LOW|MEDIUM|HIGH)$")
    notes: Optional[str] = None
