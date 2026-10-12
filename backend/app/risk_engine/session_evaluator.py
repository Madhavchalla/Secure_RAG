from datetime import datetime, timedelta, timezone
from typing import Tuple, List
from sqlalchemy.orm import Session
from app.models.audit import AuditLog, RiskAssessment


class SessionRiskEvaluator:
    """
    Evaluates temporal user session telemetry to detect probing,
    brute-force query variations, and repeated security violations.
    """

    def __init__(self, window_minutes: int = 15):
        self.window_minutes = window_minutes

    def evaluate(self, user_id: int, db: Session) -> Tuple[float, List[str]]:
        """
        Calculates Session Risk Score S_s in range [0, 100] based on recent
        denied requests and high-threat queries within the sliding window.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=self.window_minutes)

        # 1. Count recent denied or blocked actions from AuditLog
        denied_count = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.status.in_(["DENIED", "BLOCKED"]),
            AuditLog.created_at >= cutoff
        ).count()

        # 2. Count recent risk assessments where decision was BLOCK or RESTRICT
        flagged_count = db.query(RiskAssessment).filter(
            RiskAssessment.user_id == user_id,
            RiskAssessment.query_risk_score >= 40.0,
            RiskAssessment.created_at >= cutoff
        ).count()

        # Exponential scaling of session risk
        session_score = min(100.0, (25.0 * denied_count) + (15.0 * flagged_count))
        reasons = []

        if denied_count > 0:
            reasons.append(
                f"[Session Anomaly] {denied_count} denied access attempt(s) detected in the last {self.window_minutes} minutes."
            )
        if flagged_count > 0:
            reasons.append(
                f"[Session Probing] {flagged_count} suspicious or high-risk query(ies) submitted in the current session."
            )

        return session_score, reasons


# Singleton session evaluator instance
session_evaluator = SessionRiskEvaluator(window_minutes=15)
