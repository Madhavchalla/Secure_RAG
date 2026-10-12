from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: int
    filename: str
    page_number: int
    chunk_index: int
    snippet: str
    sensitivity_level: str


class RiskBreakdown(BaseModel):
    query_risk_score: float
    session_risk_score: float
    doc_sensitivity_score: float
    final_risk_score: float
    decision: str  # 'ALLOW', 'RESTRICT', 'VERIFY', 'BLOCK'
    reasons: List[str]


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1500)


class QueryResponse(BaseModel):
    query: str
    decision: str
    answer: str
    citations: List[Citation] = []
    risk_assessment: RiskBreakdown
    is_restricted: bool = False
    disclaimer: Optional[str] = None
