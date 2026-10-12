from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query_text = Column(Text, nullable=False)
    query_risk_score = Column(Float, nullable=False)
    session_risk_score = Column(Float, nullable=False)
    doc_sensitivity_score = Column(Float, nullable=False)
    final_risk_score = Column(Float, nullable=False)
    decision = Column(String(20), nullable=False)  # 'ALLOW', 'RESTRICT', 'VERIFY', 'BLOCK'
    reasons = Column(Text, nullable=False)  # JSON-encoded array of trigger explanations
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="risk_assessments")

    def __repr__(self) -> str:
        return f"<RiskAssessment id={self.id} user_id={self.user_id} score={self.final_risk_score} decision='{self.decision}'>"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)  # e.g. 'DOCUMENT_ACCESS', 'DOCUMENT_UPLOAD', 'LOGIN'
    resource_type = Column(String(50), nullable=False)  # 'DOCUMENT', 'QUERY', 'USER', 'SYSTEM'
    resource_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)  # 'SUCCESS', 'DENIED', 'WARNING'
    ip_address = Column(String(50), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action='{self.action}' status='{self.status}' at={self.created_at}>"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(50), nullable=False)  # 'PROMPT_INJECTION', 'UNAUTHORIZED_ACCESS', 'QUARANTINE_TRIGGER', 'SESSION_ANOMALY'
    severity = Column(String(20), nullable=False)  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="security_events")

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} type='{self.event_type}' severity='{self.severity}'>"
