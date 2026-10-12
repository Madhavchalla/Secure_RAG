from typing import Dict, Any, List
from app.core.config import settings


class CompositeRiskScorer:
    """
    Transparent mathematical risk scorer calculating composite risk:
    R = min(100, w_q * S_query + w_s * S_session + w_d * S_doc)
    """

    def __init__(
        self,
        w_query: float = None,
        w_session: float = None,
        w_doc: float = None
    ):
        self.w_query = w_query or settings.RISK_WEIGHT_QUERY
        self.w_session = w_session or settings.RISK_WEIGHT_SESSION
        self.w_doc = w_doc or settings.RISK_WEIGHT_DOC_SENSITIVITY

    @staticmethod
    def map_doc_sensitivity(sensitivity: str) -> float:
        """
        Map qualitative document sensitivity tier to a numerical score [0, 100].
        """
        mapping = {
            "HIGH": 75.0,
            "MEDIUM": 40.0,
            "LOW": 10.0,
        }
        return mapping.get(sensitivity.upper() if sensitivity else "LOW", 10.0)

    def calculate(
        self,
        query_score: float,
        session_score: float,
        doc_sensitivity_score: float
    ) -> float:
        """
        Calculate weighted composite risk score bounded in [0.0, 100.0].
        Applies a threat floor for critical direct injection attacks (S_query >= 80.0)
        to prevent dilution bias when session history is empty.
        """
        composite = (
            (self.w_query * query_score) +
            (self.w_session * session_score) +
            (self.w_doc * doc_sensitivity_score)
        )

        # Threat floor: Severe direct attacks (S_query >= 80) cannot be diluted
        if query_score >= 80.0:
            composite = max(composite, query_score)
        elif query_score >= 60.0:
            composite = max(composite, query_score * 0.85)

        return round(min(100.0, max(0.0, composite)), 2)


# Singleton risk scorer instance
risk_scorer = CompositeRiskScorer()
